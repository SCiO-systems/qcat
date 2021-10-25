"""
Prepare data as required for the summary frontend templates.
"""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer

from apps.configuration.configuration import QuestionnaireConfiguration
from apps.configuration.models import Project, Institution
from apps.questionnaire.models import Questionnaire, QuestionnaireLink
from apps.summary.parsers.questionnaire import QuestionnaireParser


class SummaryRenderer:
    """
    - Load summary-config according to configuration
    - annotate and aggregate values
    - add 'module' hint to create markup upon
    - sort data

    Add values / fields by following these steps:
    - in the config-json, add the summary_type and unique label.
      e.g. "summary": {
          "types": ["full"],
          "default": {
            "field_name": "location_termination_year"
          }
        }
      this will add the field 'location_termination_year' to the raw_values of
      the parser 'full'
    - add the field to the 'content' property of the renderer
    - add a method called 'definition' to the renderer, which gets the values

    """
    parser = QuestionnaireParser
    n_a = _('n.a.')

    def __init__(self, config: QuestionnaireConfiguration,
                 questionnaire: Questionnaire, quality: str,
                 base_url: str, **data):
        """
        Load full (raw) data in the same way that it is created for the API and
        apply data transformations/parsing to self.data.
        """
        self.raw_data = self.parser(
            config=config, summary_type=self.summary_type,
            questionnaire=questionnaire, n_a=self.n_a, **data
        ).data
        self.questionnaire = questionnaire
        self.quality = quality
        self.base_url = base_url

    @property
    def summary_type(self):
        """
        The name of the summary type, i.e. 'full', 'onepage'
        """
        raise NotImplementedError

    @property
    def content(self):
        """
        This is a mapping for the structure of the summary and the fields from
        the configuration with the content-types (that are important to generate
        the markup in the frontend).
        The keys such as 'header_image_image' must be set for the summary_type
        in the configuration-json.
        """
        raise NotImplementedError

    def render(self):
        """
        Render all contents, as defined by the @content property.

        """
        for section in self.content:
            method = getattr(self, section)()
            yield render_to_string(
                template_name=method['template_name'],
                context={
                    'content': method.get('partials', {}),
                    'title': method.get('title', ''),
                    'base_url': self.base_url
                }
            )


class GlobalValuesMixin:
    """
    Mixin for globally configured values

    """
    def raw_data_getter(self, key: str, value='value') -> str:
        """
        Get the first 'value' for given key from the data.
        """
        try:
            value = self.raw_data[key][0][value] if value else self.raw_data[key]
            return value or ''
        except (AttributeError, TypeError, KeyError, IndexError):
            return ''

    def string_from_list(self, key: str) -> str:
        """
        Concatenate a list of values from the data to a single string.
        """
        try:
            return ', '.join(self.raw_data[key][0].get('values', []))
        except (IndexError, KeyError):
            return ''

    def get_list_values_with_other(self, key_list_values: str, key_other: str) -> list:
        """
        Append 'other' to any list containing a dict with the keys 'highlight' 
        and 'text'
        """
        base = list(self.raw_data.get(key_list_values))
        other = self.raw_data_getter(key_other)
        if other:
            base.append({
                'highlighted': True,
                'text': other
            })
        return base

    def header_image(self):
        """
        If the header image is empty, use the first element from the default
        pictures element.
        """
        image = self.raw_data_getter('header_image_image')
        if image:
            photographer = self.raw_data_getter('header_image_photographer')
            text = '{caption} {name}'.format(
                caption=self.raw_data_getter('header_image_caption'),
                name='({})'.format(photographer) if photographer else ''
            )
        else:
            image_urls = self.raw_data_getter('images_image', value='')
            text = ''
            if image_urls:
                # use first element from photos, and remove it from the photos
                # element, so the images on display are the 'next' images.
                image_element = self.raw_data['images_image'].pop(0)
                image = image_element['value']
                text = self.get_image_caption(0)
                self.raw_data['images_caption'].pop(0)
                self.raw_data['images_photographer'].pop(0)

        return {
            'template_name': 'summary/block/header_image.html',
            'partials': {
                'image': {
                    'url': self.get_thumbnail_url(
                        image=image,
                        option_key='header_image'
                    )
                },
                'caption': {
                    'text': text
                },
                'wocat_logo_url': '{base_url}{logo}'.format(
                    base_url=self.base_url.rstrip('/'),
                    logo=static('assets/img/wocat_logo_text_shadow.svg')
                )
            }
        }

    def title(self):
        return {
            'template_name': 'summary/block/title.html',
            'partials': {
                'title': self.raw_data_getter('title_name'),
                'country': self.raw_data_getter('country'),
                'local_name': self.raw_data_getter('title_name_local'),
            }
        }

    def images(self):
        # note: data from images_image may be popped in header_image.
        image_urls = self.raw_data_getter('images_image', value='')
        images = []
        if image_urls:
            # first element is the header image, show max. 2 images.
            # Some files may not return a thumbnail and should therefore not be
            # used. Continue to loop all "images" until 2 thumbnails were
            # returned
            for index, image_data in enumerate(image_urls):
                if len(images) >= 2:
                    continue
                # If the file is a PDF, then use the preview_image instead of
                # the actual document
                if image_data['content_type'] == 'application/pdf':
                    image = image_data.get('preview_image', '')
                else:
                    image = image_data.get('value', '')
                url = self.get_thumbnail_url(
                        image=image,
                        option_key='half_height'
                    )
                if not url:
                    continue
                images.append({
                    'url': url,
                    'caption': self.get_image_caption(index)
                })
        return {
            'template_name': 'summary/block/two_images_with_caption.html',
            'partials': {
                'images': images
            }
        }

    def get_image_caption(self, index: int) -> str:
        caption = self._get_caption_info('caption', index)
        photographer = self._get_caption_info('photographer', index)
        return '{caption}{photographer}'.format(
            caption=caption or '',
            photographer=' ({})'.format(photographer) if photographer else ''
        ) or '-'

    def _get_caption_info(self, key: str, index: int) -> str:
        try:
            items = self.raw_data_getter('images_{}'.format(key), value='')[index]
            return items.get('value', '')
        except IndexError:
            return ''

    def conclusion(self):
        land_users_view = _("land user's view")
        compilers_view = _("compiler’s or other key resource person’s view")

        # Combine answers from two questions: strengths compiler and landuser
        pro_compilers = self._get_conclusion_row(
            rows=self.raw_data_getter('strengths_compiler', value='')
        )
        pro_landusers = self._get_conclusion_row(
            rows=self.raw_data_getter('strengths_landuser', value='')
        )
        # combine answers from two questions: weaknesses compiler + landuser -
        # and get the 'overcome' value as subtext
        weakness_compiler = {
            'title': compilers_view,
            'items': []
        }
        weakness_landuser = {
            'title': land_users_view,
            'items': []
        }
        weaknesses_datasets = [
            (weakness_landuser, 'weaknesses_landuser', 'weaknesses_landuser_overcome'),
            (weakness_compiler, 'weaknesses_compiler', 'weaknesses_compiler_overcome'),
        ]
        for container, key_name, overcome_name in weaknesses_datasets:
            for index, item in enumerate(self.raw_data_getter(key_name, value='')):
                subtext = self.raw_data_getter(overcome_name, value='')[index].get('value', '')
                container['items'].append({
                    'text': item['value'],
                    'subtext': subtext,
                })

        return {
            'template_name': 'summary/block/conclusion.html',
            'title': _('Conclusions and lessons learnt'),
            'partials': {
                'pro': {
                    'label': _('Strengths'),
                    'items': [
                        {
                            'title': land_users_view,
                            'items': pro_landusers
                        },
                        {
                            'title': compilers_view,
                            'items': pro_compilers
                        },
                    ]
                },
                'contra': {
                    'label': _('Weaknesses/ disadvantages/ risks'),
                    'subtext': _('how to overcome'),
                    'items': [weakness_landuser, weakness_compiler]
                }
            }
        }

    def _get_conclusion_row(self, rows: []):
        for row in rows:
            yield {'text': row['value']}

    def references(self):
        return {
            'template_name': 'summary/block/references.html',
            'title': _('References'),
            'partials': {
                'meta': {
                    'created': {
                        'title': _('Date of documentation'),
                        'value': self.questionnaire.created
                    },
                    'updated': {
                        'title': _('Last update'),
                        'value': self.questionnaire.updated
                    }
                },
                'compiler': {
                    'title': _('Compiler'),
                    'css_class': 'bullets',
                    'items': self.get_reference_person(role_name='QUESTIONNAIRE_COMPILER')
                },
                'reviewer': {
                    'title': _('Reviewer'),
                    'css_class': 'bullets',
                    'items': self.get_reference_person(role_name='QUESTIONNAIRE_REVIEWER')
                },
                'people': {
                    'title': _('Resource persons'),
                    'css_class': 'bullets',
                    'items': self.get_reference_resource_persons()
                },
                'more': {
                    'title': _('Full description in the WOCAT database'),
                    'css_class': 'bullets',
                    'items': self.get_reference_links()
                },
                'links': {
                    'title': _('Linked SLM data'),
                    'css_class': 'bullets',
                    'items': self.get_reference_linked_questionnaires()
                },
                'references': {
                    'title': _('Key references'),
                    'css_class': 'bullets',
                    'items': list(self.get_reference_articles())
                },
                'web_references': {
                    'title': _('Links to relevant information which is available online'),
                    'css_class': 'bullets',
                    'items': list(self.get_reference_web())
                },
                'project_institution': {
                    'title': _('Documentation was faciliated by'),
                    'projects': {
                        'title': _('Project'),
                        'items': self.get_projects(),
                    },
                    'institutions': {
                        'title': _('Institution'),
                        'items': self.get_institutions(),
                    }
                }
            }
        }

    def get_reference_person(self, role_name: str) -> []:
        members = self.questionnaire.questionnairemembership_set.filter(
            role=getattr(settings, role_name)
        ).select_related('user')
        if members.exists():
            return [
                {'text': '{name} ({email})'.format(
                    name=member.user.get_display_name(),
                    email=member.user.email)
                } for member in members]
        return []

    def get_reference_resource_persons(self):
        """
        Resource persons is either a dictionary with only one element or a list
        which always contains a type and either a user-id or a first/last name.
        The order of type and name correlates, so starting from the type the
        users details are appended.
        """
        resoureperson_types = self.raw_data_getter(
            'references_resourceperson_type', value=''
        )
        person_firstnames = self.raw_data_getter(
            'references_person_firstname', value=''
        )
        person_lastnames = self.raw_data_getter(
            'references_resourceperson_lastname', value=''
        )
        person_emails = self.raw_data_getter(
            'references_person_email', value=''
        )
        person_user_id = self.raw_data_getter(
            'references_resourceperson_user_id', value=''
        )
        person_types_other = self.raw_data_getter(
            'references_person_type_other', value=''
        )

        for index, person in enumerate(resoureperson_types):
            if person_user_id[index] and isinstance(person_user_id[index], dict):
                name = person_user_id[index].get('value')
                try:
                    email = get_user_model().objects.get(
                        id=person_user_id[index]['user_id']
                    ).email
                except ObjectDoesNotExist:
                    email = ''
            elif len(person_firstnames) >= index and len(person_lastnames) >= index:
                name = '{first_name} {last_name}'.format(
                    first_name=person_firstnames[index].get('value') or '',
                    last_name=person_lastnames[index].get('value') or ''
                )
                email=person_emails[index].get('value') or ''
            else:
                continue

            if person.get('values'):
                person_type = ', '.join(person.get('values', []))
            else:
                person_type = person_types_other[index].get('value', '')

            yield {'text': '{name}{email} - {type}'.format(
                name=name,
                email=' ({})'.format(email) if email else '',
                type=person_type)}

    def get_reference_links(self):
        text = '<a href="{base_url}{url}">{base_url}{url}</a>'.format(
            base_url=self.base_url.rstrip('/'),
            url=self.questionnaire.get_absolute_url())

        link_items = [
            {'text': text}
        ]

        vimeo_id = self.raw_data.get('references_vimeo_id')
        if vimeo_id and vimeo_id[0].get('value'):
            vimeo_url = 'https://player.vimeo.com/video/{}'.format(
                vimeo_id[0].get('value')
            )
            link_items.append({
                'text': '{video}: <a href="{vimeo_url}">{vimeo_url}</a>'.format(
                    video=_('Video'), vimeo_url=vimeo_url)
            })
        return link_items or [{'text': self.n_a}]

    def get_reference_linked_questionnaires(self):
        links = QuestionnaireLink.objects.filter(
            from_questionnaire=self.questionnaire,
            to_questionnaire__is_deleted=False
        )
        if not links.exists():
            yield {'text': self.n_a}
        for link in links:
            yield {'text': '{config}: {name} <a href="{base_url}{url}">{base_url}{url}</a>'.format(
                config=link.to_questionnaire.configuration.code.title(),
                name=link.to_questionnaire.get_name(),
                base_url=self.base_url.rstrip('/'),
                url=link.to_questionnaire.get_absolute_url())
            }

    def get_reference_articles(self):
        titles = self.raw_data.get('references_title', [])
        sources = self.raw_data.get('references_source', [])

        for index, title in enumerate(titles):
            if title.get('value'):
                yield {'text': '{title}: {source}'.format(
                    title=title['value'],
                    source=sources[index].get('value') or '' if sources[index] else '')}

    def get_projects(self):
        ids = self.raw_data.get('project_institution_project', [])
        return self._get_project_institutions(Project, *ids)

    def get_institutions(self):
        ids = self.raw_data.get('project_institution_institution', [])
        return self._get_project_institutions(Institution, *ids)

    def _get_project_institutions(self, model, *elements):
        ids = [item['value'] for item in elements]
        objects = model.objects.filter(id__in=ids)
        object_list = [{'title': elem, 'logo': ''} for elem in objects]
        return object_list or [{'title': self.n_a}]

    def get_reference_web(self):
        titles = self.raw_data_getter('references_links_title', value='')
        urls = self.raw_data_getter('references_links_url', value='')
        for index, title in enumerate(titles):
            yield {
                'title': title.get('value'),
                'url': urls[index].get('value')
            }

    def get_thumbnail_url(self, image: str, option_key: str) -> str:
        """
        Images can be either very large images or even pdf files. Create an
        optimized thumbnail and return its url.
        """
        if not image:
            return ''

        # full name is required to prevent a SuspiciousOperation error
        full_name = '{root}/{image}'.format(
            root=settings.MEDIA_ROOT,
            image=image[len(settings.MEDIA_URL):]
        )
        try:
            thumbnail = get_thumbnailer(full_name).get_thumbnail(
                settings.THUMBNAIL_ALIASES['summary'][self.quality][option_key],
                silent_template_exception=True
            )
        except InvalidImageFormatError:
            return ''

        # Use 'abspath' to remove '..' from path.
        media_path = os.path.abspath(settings.MEDIA_ROOT)
        #  Strip away the media folder info - only the last part is required for the url.
        file_path = thumbnail.url[thumbnail.url.find(media_path) + len(media_path):]
        return f'{self.base_url.rstrip("/")}{settings.MEDIA_URL}{file_path}'

    def get_location_values(self, *fields):
        for field in fields:
            value = self.raw_data_getter(field)
            if value:
                yield value
