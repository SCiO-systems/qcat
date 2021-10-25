from apps.configuration.editions.technologies_2018 import Technologies
from apps.configuration.models import Configuration, Translation, Value, Key, \
    Questiongroup, Category


def run():
    Technologies(
        key=Key, value=Value, questiongroup=Questiongroup,
        category=Category, configuration=Configuration, translation=Translation
    ).run_operations()
