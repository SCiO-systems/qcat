from django.utils.translation import ugettext_lazy as _

from apps.summary.parsers.approaches_2015 import Approach2015Parser
from apps.summary.renderers.summary import GlobalValuesMixin, SummaryRenderer


class Approaches2015FullSummaryRenderer(GlobalValuesMixin, SummaryRenderer):
    """
    Configuration for 'full' approaches 2015 summary.
    """
    summary_type = 'full'
    parser = Approach2015Parser

    @property
    def content(self):
        return ['header_image', 'title', 'location', 'images',
                'aims', 'participation', 'technical_support', 'financing',
                'impacts', 'conclusion', 'references']

    def location(self):
        return {
            'template_name': 'summary/block/location_approach.html',
            'title': _('Location'),
            'partials': {
                'description': {
                    'title': _('Description'),
                    'lead': self.raw_data_getter('definition'),
                    'text': self.raw_data_getter('description')
                },
                'map': {
                    'url': self.get_thumbnail_url(
                        image=self.raw_data.get('location_map_data', {}).get('img_url'),
                        option_key='map'
                    )
                },
                'infos': {
                    'location': {
                        'title': _('Location'),
                        'text': ', '.join(self.get_location_values(
                            'location_further', 'location_state_province', 'country'
                        ))
                    },
                    'geo_reference_title': _('Geo-reference of selected sites'),
                    'geo_reference': self.raw_data.get(
                        'location_map_data', {}
                    ).get('coordinates') or [self.n_a],
                    'start_date': {
                        'title': _('Initiation date'),
                        'text': self.raw_data_getter(
                            'location_initiation_year') or self.n_a
                    },
                    'end_date': {
                        'title': _('Year of termination'),
                        'text': self.raw_data_getter(
                            'location_termination_year') or self.n_a
                    },
                    'introduction': {
                        'title': _('Type of Approach'),
                        'items': self.get_list_values_with_other(
                            'location_type',
                            'location_type_other'
                        )
                    }
                }
            }
        }

    def aims(self):
        return {
            'template_name': 'summary/block/aims.html',
            'title': _('Approach aims and enabling environment'),
            'partials': {
                'main': {
                    'title': _('Main aims / objectives of the approach'),
                    'text': self.raw_data_getter('aims_main') or self.n_a
                },
                'elements': [
                    {
                        'title': _('Conditions enabling the implementation of the Technology/ ies applied under the Approach'),
                        'items': self.raw_data.get('aims_enabling') or self.n_a
                    },
                    {
                        'title': _('Conditions hindering the implementation of the Technology/ ies applied under the Approach'),
                        'items': self.raw_data.get('aims_hindering') or self.n_a
                    }
                ]
            }
        }

    def participation(self):
        lead_agency = self.raw_data_getter('participation_lead_agency')
        author = self.raw_data_getter('participation_flowchart_author')
        flowchart_preview = ''
        flowchart_data = self.raw_data.get('participation_flowchart_file', [])
        if len(flowchart_data) >= 1:
            flowchart_preview = flowchart_data[0].get('preview_image', '')
        return {
            'template_name': 'summary/block/participation.html',
            'title': _('Participation and roles of stakeholders involved'),
            'partials': {
                'stakeholders': {
                    'title': _('Stakeholders involved in the Approach and their roles'),
                    'items': list(self.raw_data.get('participation_stakeholders')),
                    'addendum': {
                        'title': _('Lead agency'),
                        'text': lead_agency
                    }
                },
                'involvement': {
                    'title': _('Involvement of local land users/ local communities in the different phases of the Approach'),
                    'partials': self.raw_data.get('participation_involvement_scale')
                },
                'involvement_items': {
                    'title': _('Involvement of local land users/ local communities in the different phases of the Approach'),
                    'partials': self.raw_data.get('participation_involvement')
                },
                'flow_chart': {
                    'url': self.get_thumbnail_url(
                        image=flowchart_preview,
                        option_key='flow_chart'
                    ),
                    'author': _('Author: {}').format(author) if author else '',
                    'title': _('Flow chart'),
                    'text': self.raw_data_getter('participation_flowchart_text')
                },
                'decision_making': {
                    'title': _('Decision-making on the selection of SLM Technology'),
                    'elements': [
                        {
                            'title': _('Decisions were taken by'),
                            'items': self.get_list_values_with_other(
                                'participation_decisions_by',
                                'participation_decisions_by_other'
                            )
                        },
                        {
                            'title': _('Decisions were made based on'),
                            'items': self.get_list_values_with_other(
                                'participation_decisions_based',
                                'participation_decisions_based_other'
                            )
                        }
                    ]
                }
            }
        }

    def technical_support(self):
        return {
            'template_name': 'summary/block/technical_support.html',
            'title': _('Technical support, capacity building, and knowledge management'),
            'partials': {
                'activities': {
                    'title': _('The following activities or services have been part of the approach'),
                    'items': [
                        self.raw_data.get('tech_support_training_is_training'),
                        self.raw_data.get('tech_support_advisory_is_advisory'),
                        self.raw_data.get('tech_support_institutions_is_institution', {}).get('bool'),
                        self.raw_data.get('tech_support_monitoring_is_monitoring'),
                        self.raw_data.get('tech_support_research_is_research')
                    ]
                },
                'training': {
                    'title': _('Capacity building/ training'),
                    'elements': [
                        {
                            'title': _('Training was provided to the following stakeholders'),
                            'items': self.get_list_values_with_other(
                                'tech_support_training_who',
                                'tech_support_training_who_other'
                            )
                        },
                        {
                            'title': _('Form of training'),
                            'items': self.get_list_values_with_other(
                                'tech_support_training_form',
                                'tech_support_training_form_other'
                            )
                        }
                    ],
                    'list': {
                        'title': _('Subjects covered'),
                        'text': self.raw_data_getter('tech_support_training_subjects')
                    }
                },
                'advisory': {
                    'title': _('Advisory service'),
                    'elements': [
                        {
                            'title': _('Advisory service was provided'),
                            'items': self.get_list_values_with_other(
                                'tech_support_advisory_service',
                                'tech_support_advisory_service_other',
                            ),
                            'description': self.raw_data_getter('tech_support_advisory_description')
                        }
                    ]
                },
                'institution_strengthening': {
                    'title': _('Institution strengthening'),
                    'subtitle': {
                        'title': _('Institutions have been strengthened / established'),
                        'value': self.raw_data.get('tech_support_institutions_is_institution', {}).get('value'),
                    },
                    'level': {
                        'title': _('at the following level'),
                        'items': self.get_list_values_with_other(
                            'tech_support_institutions_level',
                            'tech_support_institutions_level_other'
                        ),
                        'description': self.raw_data_getter('tech_support_institutions_describe'),
                        'comment_title': _('Describe institution, roles and responsibilities, members, etc.'),
                    },
                    'support_type': {
                        'title': _('Type of support'),
                        'items': self.get_list_values_with_other(
                            'tech_support_institutions_support',
                            'tech_support_institutions_support_other'
                        ),
                        'description': self.raw_data_getter('tech_support_institutions_support_specify'),
                        'comment_title': _('Further details')
                    }
                },
                'monitoring': {
                    'title': _('Monitoring and evaluation'),
                    'comment': self.raw_data_getter('tech_support_monitoring_comment'),
                },
                'research': {
                    'title': _('Research'),
                    'subtitle': _('Research treated the following topics'),
                    'items': self.get_list_values_with_other(
                        'tech_support_research_topics',
                        'tech_support_research_topics_other'
                    ),
                    'description': self.raw_data_getter('tech_support_research_details')
                }
            }
        }

    def financing(self):
        return {
            'template_name': 'summary/block/financing.html',
            'title': _('Financing and external material support'),
            'partials': {
                'budget': {
                    'title': _('Annual budget in USD for the SLM component'),
                    'items': self.raw_data.get('financing_budget'),
                    'description': self.raw_data_getter('financing_budget_comments'),
                    'addendum': _('Precise annual budget: {}'.format(self.raw_data_getter('financing_budget_precise') or self.n_a))
                },
                'services': {
                    'title': _('The following services or incentives have been provided to land users'),
                    'items': [
                        self.raw_data.get('financing_is_financing'),
                        self.raw_data.get('financing_subsidies', {}).get('is_subsidised'),
                        self.raw_data.get('financing_is_credit'),
                        self.raw_data.get('financing_is_other'),
                    ]
                },
                'subsidies': {
                    **self.raw_data.get('financing_subsidies', {}).get('subsidies'),
                    'labour': {
                        'title': _('Labour by land users was'),
                        'items': self.raw_data.get('financing_labour')
                    },
                    'material_support': {
                        'title': _('Financial/ material support provided to land users'),
                        'text': self.raw_data_getter('financing_material_support'),
                    },
                    'credit': {
                        'title': _('Credit'),
                        'items': [
                            _('Conditions: {}').format(self.raw_data_getter(
                                'financing_credit_conditions') or self.n_a
                                                       ),
                            _('Credit providers: {}').format(self.raw_data_getter(
                                'financing_credit_provider') or self.n_a
                                                             ),
                            _('Credit receivers: {}').format(self.raw_data_getter(
                                'financing_credit_receiver') or self.n_a
                                                             )
                        ]
                    },
                    'other': {
                        'title': _('Other incentives or instruments'),
                        'text': self.raw_data_getter('financing_other_text') or self.n_a
                    }
                }
            }
        }

    def impacts(self):
        return {
            'template_name': 'summary/block/impacts_approach.html',
            'title': _('Impact analysis and concluding statements'),
            'partials': {
                'impacts': {
                    'title': _('Impacts of the Approach'),
                    'subtitle': _('Did the approach...'),
                    'items': self.raw_data.get('impacts_impacts'),
                },
                'motivation': {
                    'title': _('Main motivation of land users to implement SLM'),
                    'items': self.get_list_values_with_other(
                        'impacts_motivation',
                        'impacts_motivation_other'
                    ) or [{'text': self.n_a, 'highlighted': True}]
                },
                'sustainability': {
                    'title': _('Sustainability of Approach activities'),
                    'subtitle': _('Can the land users sustain what hat been implemented through the Approach (without external support)?'),
                    'items': self.raw_data.get('impacts_sustainability'),
                    'comment': self.raw_data_getter('impacts_sustainability_comments')
                }
            }
        }
