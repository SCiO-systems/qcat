from django.utils.translation import ugettext_lazy as _

from apps.summary.parsers.technologies_2015 import Technology2015Parser
from apps.summary.renderers.summary import GlobalValuesMixin, SummaryRenderer


class Technology2015FullSummaryRenderer(GlobalValuesMixin, SummaryRenderer):
    """
    Configuration for 'full' technology 2015 summary.
    """
    parser = Technology2015Parser
    summary_type = 'full'

    @property
    def content(self):
        return ['header_image', 'title', 'location', 'images',
                'classification', 'technical_drawing', 'establishment_costs',
                'natural_environment', 'human_environment', 'impacts',
                'cost_benefit', 'climate_change', 'adoption_adaptation',
                'conclusion', 'references']

    def header_image(self):
        data = super().header_image()
        if self.raw_data_getter('header_image_sustainability') == _('Yes'):
            data['partials']['note'] = _(
                'This technology is problematic with regard to land '
                'degradation, so it cannot be declared a sustainable land '
                'management technology')
        return data

    def location(self):
        year = self.raw_data_getter('location_implementation_year')
        decade = self.string_from_list('location_implementation_decade')
        spread = self.string_from_list('location_spread')
        spread_area = self.string_from_list('location_spread_area')
        if spread_area:
            spread = f'{spread} ({_("approx.")} {spread_area})'

        return {
            'template_name': 'summary/block/location.html',
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
                            'location_further', 'location_state_province', 'country')
                        )
                    },
                    'sites': {
                        'title': _('No. of Technology sites analysed'),
                        'text': self.string_from_list('location_sites_considered')
                    },
                    'geo_reference_title': _('Geo-reference of selected sites'),
                    'geo_reference': self.raw_data.get(
                        'location_map_data', {}
                    ).get('coordinates') or [self.n_a],
                    'spread': {
                        'title': _('Spread of the Technology'),
                        'text': spread
                    },
                    'date': {
                        'title': _('Date of implementation'),
                        'text': '{year}{decade}'.format(
                            year=year,
                            decade='; {}'.format(decade) if year and decade else decade
                        )
                    },
                    'introduction': {
                        'title': _('Type of introduction'),
                        'items': self.get_list_values_with_other(
                            'location_who_implemented',
                            'location_who_implemented_other'
                        )
                    }
                }
            }
        }

    def classification(self):
        try:
            slm_group = self.raw_data_getter(
                'classification_slm_group', value=''
            )[0].get('values')
            # structure as required for an unordered list.
            slm_group = [{'text': text} for text in slm_group]
        except (KeyError, IndexError):
            slm_group = [{'text': self.n_a}]

        slm_group_other = self.raw_data_getter('classification_slm_group_other')
        if slm_group_other:
            slm_group.append({'text': slm_group_other})

        # append various 'other' fields
        purpose = list(self.raw_data.get('classification_main_purpose'))
        purpose_other = self.raw_data_getter('classification_main_purpose_other')
        if purpose_other:
            purpose.append({'highlighted': True, 'text': purpose_other})
        water_supply = list(self.raw_data.get('classification_watersupply'))
        water_supply_other = self.raw_data_getter('classification_watersupply_other')
        if water_supply_other:
            water_supply.append({'highlighted': True, 'text': water_supply_other})

        return {
            'template_name': 'summary/block/classification.html',
            'title': _('Classification of the Technology'),
            'partials': {
                'main_purpose': {
                    'title': _('Main purpose'),
                    'partials': purpose
                },
                'landuse': {
                    'title': _('Land use'),
                    'partials': self.raw_data.get('classification_landuse')
                },
                'water_supply': {
                    'title': _('Water supply'),
                    'partials': {
                        'list': water_supply,
                        'text': [
                            {
                                'title': _('Number of growing seasons per year'),
                                'text': self.string_from_list('classification_growing_seasons') or self.n_a
                            },
                            {
                                'title': _('Land use before implementation of the Technology'),
                                'text': self.raw_data_getter('classification_lu_before') or self.n_a
                            },
                            {
                                'title': _('Livestock density'),
                                'text': self.raw_data_getter('classification_livestock') or self.n_a
                            }
                        ]
                    }
                },
                'purpose': {
                    'title': _('Purpose related to land degradation'),
                    'partials': self.raw_data.get('classification_purpose')
                },
                'degredation': {
                    'title': _('Degradation addressed'),
                    'partials': self.raw_data.get('classification_degradation')
                },
                'slm_group': {
                    'title': _('SLM group'),
                    'partials': slm_group
                },
                'measures': {
                    'title': _('SLM measures'),
                    'partials': self.raw_data.get('classification_measures') or self.n_a
                }
            }
        }

    def technical_drawing(self):
        drawing_files = self.raw_data.get('tech_drawing_image', [])
        drawing_authors = self.raw_data.get('tech_drawing_author', [])
        main_drawing = {}
        additional_drawings = []

        for index, file in enumerate(drawing_files):
            preview = file.get('preview_image')
            if preview:
                try:
                    author = drawing_authors[index]['value']
                except (KeyError, IndexError):
                    author = ''

                author_title = _('Author: {}').format(author) if author else ''

                if index == 0:
                    main_drawing = {
                        'url': self.get_thumbnail_url(preview, 'flow_chart'),
                        'author': author_title
                    }
                else:
                    additional_drawings.append({
                        'url': self.get_thumbnail_url(preview, 'flow_chart_half_height'),
                        'caption': author_title
                    })

        return {
            'template_name': 'summary/block/specifications.html',
            'title': _('Technical drawing'),
            'partials': {
                'title': _('Technical specifications'),
                'text': self.raw_data_getter('tech_drawing_text'),
                'main_drawing': main_drawing,
                'images': additional_drawings
            }
        }

    def establishment_costs(self):
        base = self.string_from_list('establishment_cost_calculation_base')

        perarea_size = self.raw_data_getter('establishment_perarea_size')
        perarea_conversion = self.raw_data_getter('establishment_perarea_unit_conversion')

        perunit_unit = self.raw_data_getter('establishment_perunit_unit')
        perunit_volume = self.raw_data_getter('establishment_perunit_volume')

        # chose explanation text according to selected calculation type.
        extra = ''
        if perarea_size:
            conversion_text = _('; conversion factor to one hectare: <b>1 ha = {}</b>').format(perarea_conversion)
            extra = _(' (size and area unit: <b>{}</b>{})').format(
                perarea_size,
                conversion_text if perarea_conversion else ''
            )
        if perunit_unit:
            perunit_text = _('unit: <b>{}</b>').format(perunit_unit)
            extra = ' ({}{})'.format(
                perunit_text,
                ' volume, length: <b>{}</b>'.format(perunit_volume) if perunit_volume else ''
            )

        title_addendum = ''
        if perarea_size or perunit_unit:
            title_addendum = ' (per {})'.format(perarea_size or perunit_unit)

        calculation = '{base}{extra}'.format(
            base=base,
            extra=extra
        )
        usd = self.string_from_list('establishment_dollar')
        national_currency = self.raw_data_getter('establishment_national_currency')
        currency = usd or national_currency or self.n_a
        wage = self.raw_data_getter('establishment_average_wage') or _('n.a')
        exchange_rate = self.raw_data_getter('establishment_exchange_rate') or _('n.a')

        return {
            'template_name': 'summary/block/establishment_and_maintenance.html',
            'title': _('Establishment and maintenance: activities, inputs and costs'),
            'partials': {
                'introduction': {
                    'title': _('Calculation of inputs and costs'),
                    'items': [
                        _('Costs are calculated: {}').format(calculation),
                        _('Currency used for cost calculation: <b>{}</b>').format(currency),
                        _('Exchange rate (to USD): 1 USD = {} {}').format(
                            exchange_rate,
                            national_currency if national_currency else ''
                        ),
                        _('Average wage cost of hired labour per day: {}').format(wage)
                    ],
                    'main_factors': self.raw_data_getter('establishment_determinate_factors') or self.n_a,
                    'main_factors_title': _('Most important factors affecting the costs')
                },
                'establishment': {
                    'title': _('Establishment activities'),
                    'list': list(self._get_establishment_list_items('establishment')),
                    #'comment': self.raw_data_getter('establishment_input_comments'),
                    'table': {
                        'title': _('Establishment inputs and costs{}').format(title_addendum),
                        'total_cost_estimate': self.raw_data_getter(
                            'establishment_total_estimation'
                        ),
                        'total_cost_estimate_title': _(
                            'Total establishment costs (estimation)'
                        ),
                        'unit': perunit_unit,
                        'currency': currency,
                        **self.raw_data.get('establishment_input', {}),
                    }
                },
                'maintenance': {
                    'title': _('Maintenance activities'),
                    'list': list(self._get_establishment_list_items('maintenance')),
                    #'comment': self.raw_data_getter('establishment_maintenance_comments'),
                    'table': {
                        'title': _('Maintenance inputs and costs{}').format(title_addendum),
                        'total_cost_estimate': self.raw_data_getter(
                            'establishment_maintenance_total_estimation'
                        ),
                        'total_cost_estimate_title': _(
                            'Total maintenance costs (estimation)'
                        ),
                        'unit': perunit_unit,
                        'currency': currency,
                        **self.raw_data.get('maintenance_input', {}),
                    }
                }
            }
        }

    def _get_establishment_list_items(self, content_type: str):
        """
        Combine measure type and timing for identical question groups.
        """
        activity = 'establishment_{}_activities'.format(content_type)
        timing = 'establishment_{}_timing'.format(content_type)
        timing_title = _('Timing/ frequency')
        for index, activity in enumerate(self.raw_data.get(activity, [])):

            try:
                addendum = f' ({timing_title}: {self.raw_data[timing][index]["value"]})'
            except (KeyError, IndexError):
                addendum = ''

            yield {
                'text': '{activity}{addendum}'.format(
                    activity=activity['value'] or '',
                    addendum=addendum
                )}

    def natural_environment(self):
        specifications = ''
        climate_zone_text = self.raw_data_getter('natural_env_climate_zone_text')
        rainfall = self.raw_data_getter('natural_env_rainfall_annual')
        rainfall_specifications = self.raw_data_getter('natural_env_rainfall_specifications')
        meteostation = self.raw_data_getter('natural_env_rainfall_meteostation')

        if rainfall:
            rainfall = _('Average annual rainfall in mm: {}').format(rainfall)
        if meteostation:
            meteostation = _('Name of the meteorological station: {}').format(meteostation)

        for text in [rainfall, rainfall_specifications, meteostation, climate_zone_text]:
            if text:
                specifications += text + '\n'

        return {
            'template_name': 'summary/block/natural_environment.html',
            'title': _('Natural environment'),
            'partials': {
                'rainfall': {
                    'title': _('Average annual rainfall'),
                    'items': self.raw_data.get('natural_env_rainfall')
                },
                'zone': {
                    'title': _('Agro-climatic zone'),
                    'items': self.raw_data.get('natural_env_climate_zone')
                },
                'specifications': {
                    'title': _('Specifications on climate'),
                    'text': specifications or self.n_a
                },
                'slope': {
                    'title': _('Slope'),
                    'items': self.raw_data.get('natural_env_slope')
                },
                'landforms': {
                    'title': _('Landforms'),
                    'items': self.raw_data.get('natural_env_landforms')
                },
                'altitude': {
                    'title': _('Altitude'),
                    'items': self.raw_data.get('natural_env_altitude')
                },
                'convex': {
                    'title': _('Technology is applied in'),
                    'items': self.raw_data.get('natural_env_convex_concave')
                },
                'soil_depth': {
                    'title': _('Soil depth'),
                    'items': self.raw_data.get('natural_env_soil_depth')
                },
                'soil_texture_top': {
                    'title': _('Soil texture (topsoil)'),
                    'items': self.raw_data.get('natural_env_soil_texture')
                },
                'soil_texture_below': {
                    'title': _('Soil texture (> 20 cm below surface)'),
                    'items': self.raw_data.get('natural_env_soil_texture_below')
                },
                'topsoil': {
                    'title': _('Topsoil organic matter content'),
                    'items': self.raw_data.get('natural_env_soil_organic')
                },
                'groundwater': {
                    'title': _('Groundwater table'),
                    'items': self.raw_data.get('natural_env_groundwater')
                },
                'surface_water': {
                    'title': _('Availability of surface water'),
                    'items': self.raw_data.get('natural_env_surfacewater')
                },
                'water_quality': {
                    'title': _('Water quality (untreated)'),
                    'items': self.raw_data.get('natural_env_waterquality')
                },
                'flooding': {
                    'title': _('Occurrence of flooding'),
                    'items': self.raw_data.get('natural_env_flooding')
                },
                'salinity': {
                    'title': _('Is salinity a problem?'),
                    'items': self.raw_data.get('natural_env_salinity')
                },
                'species': {
                    'title': _('Species diversity'),
                    'items': self.raw_data.get('natural_env_species')
                },
                'habitat': {
                    'title': _('Habitat diversity'),
                    'items': self.raw_data.get('natural_env_habitat')
                }
            }
        }

    def human_environment(self):
        return {
            'template_name': 'summary/block/human_environment.html',
            'title': _('Characteristics of land users applying the Technology'),
            'partials': {
                'market': {
                    'title': _('Market orientation'),
                    'items': self.raw_data.get('human_env_market_orientation')
                },
                'income': {
                    'title': _('Off-farm income'),
                    'items': self.raw_data.get('human_env_offfarm_income')
                },
                'wealth': {
                    'title': _('Relative level of wealth'),
                    'items': self.raw_data.get('human_env_wealth')
                },
                'mechanization': {
                    'title': _('Level of mechanization'),
                    'items': self.raw_data.get('human_env_mechanisation')
                },
                'sedentary': {
                    'title': _('Sedentary or nomadic'),
                    'items': self.get_list_values_with_other(
                        'human_env_sedentary_nomadic',
                        'human_env_sedentary_nomadic_other'
                    )
                },
                'individuals': {
                    'title': _('Individuals or groups'),
                    'items': self.raw_data.get('human_env_individuals')
                },
                'gender': {
                    'title': _('Gender'),
                    'items': self.raw_data.get('human_env_gender')
                },
                'age': {
                    'title': _('Age'),
                    'items': self.raw_data.get('human_env_age')
                },
                'area': {
                    'title': _('Area used per household'),
                    'items': self.raw_data.get('human_env_land_size')
                },
                'scale': {
                    'title': _('Scale'),
                    'items': self.raw_data.get('human_env_land_size_relative')
                },
                'ownership': {
                    'title': _('Land ownership'),
                    'items': self.get_list_values_with_other(
                        'human_env_ownership',
                        'human_env_ownership_other'
                    )
                },
                'land_rights': {
                    'title': _('Land use rights'),
                    'items': self.get_list_values_with_other(
                        'human_env_landuser_rights',
                        'human_env_landuser_rights_other'
                    )
                },
                'water_rights': {
                    'title': _('Water use rights'),
                    'items': self.get_list_values_with_other(
                        'human_env_wateruser_rights',
                        'human_env_wateruser_rights_other'
                    )
                },
                'access': {
                    'title': _('Access to services and infrastructure'),
                    'items': self.raw_data.get('human_env_services')
                }
            }
        }

    def impacts(self):
        return {
            'template_name': 'summary/block/impacts.html',
            'title': _('Impacts'),
            'partials': {
                'economic': {
                    'title': _('Socio-economic impacts'),
                    'items': self.raw_data.get('impacts_cropproduction'),
                },
                'cultural': {
                    'title': _('Socio-cultural impacts'),
                    'items': self.raw_data.get('impacts_foodsecurity')
                },
                'ecological': {
                    'title': _('Ecological impacts'),
                    'items': self.raw_data.get('impacts_soilmoisture')
                },
                'off_site': {
                    'title': _('Off-site impacts'),
                    'items': self.raw_data.get('impacts_downstreamflooding')
                }
            }
        }

    def cost_benefit(self):
        return {
            'template_name': 'summary/block/cost_benefit_analysis.html',
            'title': _('Cost-benefit analysis'),
            'partials': {
                'establishment': {
                    'title': _('Benefits compared with establishment costs'),
                    'items': self.raw_data.get(
                        'impacts_establishment_costbenefit')
                },
                'maintenance': {
                    'title': _('Benefits compared with maintenance costs'),
                    'items': self.raw_data.get(
                        'impacts_maintenance_costbenefit')
                },
                'comment': self.raw_data_getter('tech_costbenefit_comment')
            }
        }

    def climate_change(self):
        return {
            'template_name': 'summary/block/climate_change.html',
            'title': _('Climate change'),
            'labels': {
                'left': _('Climate change/ extreme to which the Technology is exposed'),
                'right': _('How the Technology copes with these changes/extremes')
            },
            'partials': self.raw_data.get('climate_change'),
        }

    def adoption_adaptation(self):
        return {
            'template_name': 'summary/block/adoption_adaptation.html',
            'title': _('Adoption and adaptation'),
            'partials': {
                'adopted': {
                    'title': _('Percentage of land users in the area who have adopted the Technology'),
                    'items': self.raw_data.get('adoption_percentage')
                },
                'adopted_no_incentive': {
                    'title': _('Of all those who have adopted the Technology, how many have done so without receiving material incentives?'),
                    'items': self.raw_data.get('adoption_spontaneously')
                },
                'quantify': {
                    'title': _('Number of households and/ or area covered'),
                    'text': self.raw_data_getter('adoption_quantify')
                },
                'adaptation': {
                    'title': _('Has the Technology been modified recently to adapt to changing conditions?'),
                    'items': self.raw_data.get('adoption_modified')
                },
                'condition': {
                    'title': _('To which changing conditions?'),
                    'items': self.get_list_values_with_other(
                        'adoption_condition',
                        'adoption_condition_other'
                    )
                },
                'comments': self.raw_data_getter('adoption_comments')
            }
        }
