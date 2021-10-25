import contextlib
import logging

import requests
from os.path import join, isfile

from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.translation import get_language
import bs4
from apps.summary.renderers.approaches_2015 import Approaches2015FullSummaryRenderer
from apps.summary.renderers.technologies_2015 import \
    Technology2015FullSummaryRenderer
from apps.summary.renderers.technologies_2018 import \
    Technology2018FullSummaryRenderer

from wkhtmltopdf.views import PDFTemplateView, PDFTemplateResponse

from apps.questionnaire.models import Questionnaire
from apps.questionnaire.utils import get_query_status_filter, \
    get_questionnaire_data_in_single_language

logger = logging.getLogger(__name__)


class CachedPDFTemplateResponse(PDFTemplateResponse):
    """
    Creating the pdf includes two resource-heavy processes:
    - extracting the json to markup (frontend)
    - call to wkhtmltopdf (backend)

    Therefore, the content is created only once per filename (which should
    distinguish between new questionnaire edits). This only works with
    reasonably precise file names!
    """
    @property
    def file_path(self):
        return join(settings.SUMMARY_PDF_PATH, self.filename)

    def get_rendered_content(self):
        return super().rendered_content

    def content_with_file_cache(self):
        if isfile(self.file_path):
            # Catch any exception, worst case is that the pdf is created from
            # scratch again
            with contextlib.suppress(Exception) as e:
                return open(self.file_path, 'rb').read()

        content = self.get_rendered_content()
        with contextlib.suppress(Exception) as e:
            open(self.file_path, 'wb').write(content)
        return content

    @property
    def rendered_content(self):
        if settings.DEBUG:
            return self.get_rendered_content()
        else:
            return self.content_with_file_cache()


class RawTemplateResponse(TemplateResponse):
    """
    Create HTML with the default template response, cast the markup to a table. 
    """

    def rows_to_tr(self):
        """
        Prepend a row with 12 elements, forcing 'proper' width of following rows
        """
        for row in self.soup.select('.row'):
            table = self.soup.new_tag('table')
            table.attrs['width'] = '100%'
            row.wrap(table)
            grid_12_columns = '<tr>'
            for i in range(0, 12):
                grid_12_columns += '<td width="8.3%"></td>'
            grid_12_columns += '</tr>'
            row.insert_before(bs4.BeautifulSoup(grid_12_columns, 'lxml'))
            if 'range' not in row.attrs['class']:
                row.unwrap()

    def columns_to_td(self):
        """
        Use columns-width as colspan.
        """
        for column in self.soup.select('.columns'):
            column.name = 'td'

            for i, class_name in enumerate(column.attrs['class']):
                if class_name.startswith('small'):
                    # Use number of grid rows for colspan
                    column.attrs['colspan'] = class_name[6:]
                    del column.attrs['class'][i]

    def highlight_list_to_bold(self):
        """
        CSS highlights can not be seen in word, make them bold.
        """
        for highlight in self.soup.select('.highlights_list > .true'):
            highlight.wrap(self.soup.new_tag('strong'))

    def header_image_to_foreground(self):
        """
        Copy the background-image to the front, so it is copied automatically.
        """
        header = self.soup.select('div.header-img')
        if header:
            style_tag = header[0].attrs['style']
            url = style_tag[style_tag.index('(') + 1:-1]
            image = self.soup.new_tag('img', src=url, **{'class': 'header-img'})
            header[0].attrs['style'] = ''
            header[0].insert(0, image)

    def range_to_table(self):
        """
        Cast the 'ranges' to a more basic format: wrap the parent container with a table, and 
        cast the divs to tds.
        """
        for range_min in self.soup.select('.range_min'):
            range_container = range_min.parent.parent

            range_table = self.soup.new_tag('table')
            range_container.insert(0, range_table)

            for i, div in enumerate(range_container.select('div')):
                div.name = 'td'
                extracted = div.extract()
                range_table.insert(i, extracted)

        for selected in self.soup.select('.range_true'):
            selected.insert(0, bs4.NavigableString('x'))

    def normalize_rotated_range(self):
        """
        Normalize 'rotated' ranges, indicated by the class 'vertical-title'
        """
        for container in self.soup.select('.vertical-title'):

            # Extract the labels from the header.
            for header_labels in container.select('.rotate'):
                labels = []
                header_labels.wrap(self.soup.new_tag('table'))
                for div in header_labels.select('div'):
                    labels.append(div.text)

                # Fill in the checked value as text, remove all ranges.
                for sibling in container.find_next_siblings('div'):
                    squares = sibling.select('.range_square')
                    if squares:
                        # Get the position of the selected element
                        for i, square in enumerate(squares[0].parent.select('div')):
                            if 'range_true' in square.get('class', []):
                                # Print the text-label
                                squares[0].parent.parent.insert(0, bs4.NavigableString(labels[i]))

                        # Remove the squares.
                        squares[0].parent.decompose()

            # Remove the header row.
            container.decompose()

        # Remove the additional lines with 'hr' tags.
        for inline_comment in self.soup.select('.inline-comment'):
            for hr in inline_comment.select('hr'):
                hr.parent.decompose()

    def approach_flow_chart_header(self):
        """
        Move chart to bottom of the text.

        """
        flow_chart_container = self.soup.select('.approach-flow-chart')
        if flow_chart_container:
            image = flow_chart_container[0].select('.img_in_text')
            if image:
                flow_chart_container[0].insert(-1, image[0].extract())

    def html_to_table(self, html: str) -> str:
        """
        Cast the 'fluid' markup to a table so the word-document looks
        as expected by the researchers.
        """
        self.soup = bs4.BeautifulSoup(html, 'lxml')
        css = self.soup.find('link')
        # Cache busting is only done with respect to 'summary.css', so in case
        # changes on the summary_raw.css are made, also change a blank in
        # 'summary.css'.
        css.attrs['href'] = css.attrs['href'].replace(
            'summary.css', 'summary_raw.css'
        )
        self.header_image_to_foreground()
        self.approach_flow_chart_header()
        self.highlight_list_to_bold()
        self.columns_to_td()
        self.range_to_table()
        self.normalize_rotated_range()
        self.rows_to_tr()
        return str(self.soup)

    @property
    def rendered_content(self):
        return self.html_to_table(super().rendered_content)


class SummaryPDFCreateView(PDFTemplateView):
    """
    Put the questionnaire data to the context and return the rendered pdf.
    """
    response_class = CachedPDFTemplateResponse
    doc_response_class = RawTemplateResponse
    summary_type = 'full'  # Only one summary type is available right now
    base_template_path = 'summary/'
    http_method_names = ['get']
    render_classes = {
        'technologies_2018': {'full': Technology2018FullSummaryRenderer},
        'technologies_2015': {'full': Technology2015FullSummaryRenderer},
        'approaches_2015': {'full': Approaches2015FullSummaryRenderer}
    }
    footer_template = '{}layout/footer.html'.format(base_template_path)
    # see: http://wkhtmltopdf.org/usage/wkhtmltopdf.txt
    cmd_options = {
        'dpi': '96',
        'margin-top': '1cm',
        'margin-bottom': '1cm',
    }
    default_quality = 'screen'

    @property
    def is_doc_file(self):
        return self.request.GET.get('as', '') == 'doc'

    @property
    def css_class(self):
        return f'is-{self.questionnaire.configuration.code}'

    def get(self, request, *args, **kwargs):
        self.questionnaire = self.get_object(questionnaire_id=self.kwargs['id'])
        self.quality = self.request.GET.get('quality', self.default_quality)
        # filename is set withing render_to_response, this is too late as it's
        # used for caching.
        self.filename = self.get_filename()
        if self.is_doc_file:
            self.response_class = self.doc_response_class
        self.track_request()
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        template = self.request.GET.get('template', 'base')
        return '{}/layout/{}.html'.format(self.base_template_path, template)

    def get_filename(self) -> str:
        """
        The filename is specific enough to be used as 'pseudo cache-key' in the
        CachedPDFTemplateResponse.
        """
        return 'wocat-{identifier}-{edition}-{language}-{summary_type}-' \
               '{quality}-{update}.pdf'.format(
            identifier=self.questionnaire.id,
            edition=self.questionnaire.configuration.id,
            language=get_language(),
            summary_type=self.summary_type,
            quality=self.quality,
            update=self.questionnaire.updated.strftime('%Y-%m-%d-%H-%M')
        )

    def get_object(self, questionnaire_id: int) -> Questionnaire:
        """
        Get questionnaire and check status / permissions.
        """
        status_filter = get_query_status_filter(self.request)
        status_filter &= Q(id=questionnaire_id)
        obj = Questionnaire.with_status.not_deleted().filter(
            Q(id=questionnaire_id), status_filter
        ).distinct()
        if not obj.exists() or obj.count() != 1:
            raise Http404
        return obj.first()

    def get_summary_data(self, **data):
        """
        Get summary data from renderer according to configuration.
        """
        identifier = f'{self.questionnaire.configuration.code}_' \
                     f'{self.questionnaire.configuration.edition}'
        try:
            renderer = self.render_classes[identifier][self.summary_type]
        except KeyError:
            raise Http404
        return renderer(
            config=self.questionnaire.configuration_object,
            questionnaire=self.questionnaire,
            quality=self.quality,
            base_url=self.request.build_absolute_uri('/'), **data
        ).render()

    def get_prepared_data(self, questionnaire: Questionnaire) -> dict:
        """
        Load the prepared JSON for given object in the current language.
        """
        data = get_questionnaire_data_in_single_language(
            questionnaire_data=questionnaire.data,
            locale=get_language(),
            original_locale=questionnaire.original_locale
        )
        return self.get_summary_data(**data)

    def get_footer_context(self) -> dict:
        """
        Provide variables used in the footer template.
        """
        name = self.questionnaire.get_name()
        if len(name) > 70:
            name = '{}...'.format(name[:67])
        return {
            'footer_name': name,
            'footer_config': self.questionnaire.configuration.code.title()
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['css_file_hash'] = apps.get_app_config('summary').css_file_hash
        context['css_class'] = self.css_class
        context['sections'] = self.get_prepared_data(self.questionnaire)
        context.update(self.get_footer_context())
        # For languages with no spaces between words (e.g. Lao, Khmer), add CSS
        # line break rule if either the questionnaire or its original version is
        # in one of these languages.
        if self.questionnaire.original_locale in settings.WORD_WRAP_LANGUAGES \
                or self.request.LANGUAGE_CODE in settings.WORD_WRAP_LANGUAGES:
            context['break_words'] = True
        return context

    def track_request(self):
        """
        Submit a summary-download event to matomo.
        """
        if settings.PIWIK_SITE_ID:
            # Downloads are not properly registered for relative urls, so build the complete url.
            url = f'{self.request.scheme}://{self.request.META["HTTP_HOST"]}{self.request.path}'
            payload = dict(
                idsite=settings.PIWIK_SITE_ID,
                token_auth=settings.PIWIK_AUTH_TOKEN,
                rec=1,
                apiv=1,
                url=url,
                download=url
            )

            if self.request.user.is_authenticated():
                payload['_id'] = self.request.user.id

            if settings.DEBUG:
                # Also see https://developer.matomo.org/api-reference/tracking-api >
                # Debugging the Tracker
                payload['debug'] = 1

            try:
                requests.get(f'{settings.PIWIK_URL}matomo.php', params=payload)
            except Exception:  # Don't raise any kind of exception for failed tracking.
                logger.error(
                    f'Cannot track summary download for url %s (%s)',
                    f'{settings.PIWIK_URL}matomo.php', payload
                )
