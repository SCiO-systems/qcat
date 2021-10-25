from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from apps.summary.parsers.technologies_2018 import Technology2018Parser
from apps.summary.renderers.technologies_2015 import \
    Technology2015FullSummaryRenderer


class Technology2018FullSummaryRenderer(Technology2015FullSummaryRenderer):
    """
    Configuration for 'full' technologies 2018 summary.
    """

    parser = Technology2018Parser

    def technical_drawing(self):
        # No more separate repeating drawing-questiongroup and single
        # specifications text questiongroup. Instead, repeating questiongroups
        # with drawing and specifications together.
        drawing_files = self.raw_data.get('tech_drawing_image', [])
        drawing_authors = self.raw_data.get('tech_drawing_author', [])
        drawing_texts = self.raw_data.get('tech_drawing_text', [])

        drawings = []

        for index, file in enumerate(drawing_files):
            preview = file.get('preview_image')
            if preview:
                try:
                    author = drawing_authors[index]['value']
                except (KeyError, IndexError):
                    author = ''

                try:
                    text = drawing_texts[index]['value']
                except (KeyError, IndexError):
                    text = ''

                author_title = f"{_('Author:')} {author}" if author else ''

                drawings.append({
                    'url': self.get_thumbnail_url(preview, 'flow_chart'),
                    'author': author_title,
                    'text': text,
                })

        return {
            'template_name': 'summary/tech_2018/block/specifications.html',
            'title': _('Technical drawing'),
            'partials': {
                'title': _('Technical specifications'),
                'drawings': drawings,
            }
        }

    def get_reference_person(self, role_name: str) -> []:
        members = self.questionnaire.questionnairemembership_set.filter(
            role=getattr(settings, role_name)
        ).select_related('user')
        if members.exists():
            return [
                {'text': member.user.get_display_name()} for member in members]
        return []

    def get_reference_resource_persons(self):
        """
        Resource persons is either a dictionary with only one element or a list
        which always contains a type and either a user-id or a first/last name.
        The order of type and name correlates, so starting from the type the
        users details are appended.

        Changes in edition 2018: e-mail was removed.
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
        person_user_id = self.raw_data_getter(
            'references_resourceperson_user_id', value=''
        )
        person_types_other = self.raw_data_getter(
            'references_person_type_other', value=''
        )

        for index, person in enumerate(resoureperson_types):
            if person_user_id[index] and isinstance(person_user_id[index], dict):
                name = person_user_id[index].get('value')
            elif len(person_firstnames) >= index and len(person_lastnames) >= index:
                name = '{first_name} {last_name}'.format(
                    first_name=person_firstnames[index].get('value') or '',
                    last_name=person_lastnames[index].get('value') or ''
                )
            else:
                continue

            if person.get('values'):
                person_type = ', '.join(person.get('values', []))
            else:
                person_type = person_types_other[index].get('value', '')

            yield {'text': '{name} - {type}'.format(
                name=name,
                type=person_type)}

    def location(self):
        location_data = super().location()

        # Use new template
        location_data['template_name'] = 'summary/tech_2018/block/location.html'

        # New question about precise area was added. Use this value if
        # available, else the approximate range (as before).
        spread_area_precise = self.raw_data_getter(
            'location_spread_area_precise')
        if spread_area_precise:
            spread = self.string_from_list('location_spread')
            location_data['partials']['infos']['spread']['text'] = \
                f'{spread} ({spread_area_precise} {_("km²")})'

        # New question about location in permanently protected area was added.
        location_data['partials']['infos']['protected_area'] = {
            'title': _('In a permanently protected area?'),
            'text': self.raw_data_getter('location_protected_area'),
        }

        return location_data

    def classification(self):
        classification_data = super().classification()

        # Use new template
        classification_data['template_name'] = 'summary/tech_2018/block/classification.html'

        # Current land use: Add new question about mixed land use
        classification_data['partials']['landuse'] = {
            'title': _('Land use'),
            'partials': {
                'landuse': {
                    'list': self.raw_data.get('classification_landuse_current'),
                },
                'mixed': {
                    'text': self.raw_data.get('landuse_current_mixed'),
                }
            },
        }

        # Remove questions about growing seasons (moved), initial land use
        # (moved) and livestock density (deleted).
        del classification_data['partials']['water_supply']['partials']['text']

        return classification_data

    def natural_environment(self):
        data = super().natural_environment()

        # Add information about whether water quality refers to ground or
        # surface water
        water_quality_ref_data = self.raw_data.get(
            'natural_env_waterquality_ref')
        if water_quality_ref_data:
            ref_data = water_quality_ref_data[0]
            data['partials']['water_quality']['referring'] = f"{ref_data['key']} {', '.join(ref_data['values'])}"

        return data

    def human_environment(self):
        data = super().human_environment()

        # Overwrite template to show comments of 5.9 (access to services and
        # infrastructure)
        data['template_name'] = 'summary/tech_2018/block/human_environment.html'

        # Add comments of 5.9
        services_comments_data = self.raw_data.get('human_env_services_comments')
        if services_comments_data:
            comments = services_comments_data[0]
            data['partials']['access']['comments'] = {
                'title': comments['key'],
                'text': comments['value'],
            }

        return data
