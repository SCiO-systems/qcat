from apps.configuration.editions.sample_2018 import Sample
from apps.configuration.models import Configuration, Translation, Value, Key, \
    Questiongroup, Category


def run():
    Sample(
        key=Key, value=Value, questiongroup=Questiongroup,
        category=Category, configuration=Configuration, translation=Translation
    ).run_operations()
