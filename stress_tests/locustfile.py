import random

from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):
    """
    Typical tasks that users perform.
    This should also touch all included components (db, elasticsearch, login api).
    """
    def on_start(self):
        # maybe: use environment variables
        self.approaches = ['approaches_490']
        self.technologies = ['technologies_784']
        self.unccd = ['unccd_156']
        self.summary_ids = [785, 491]
        self.user_id = 3088
        self.languages = ['en', 'fr', 'es', 'ru', 'km', 'lo', 'ar', 'pt', 'af']

    @property
    def language(self):
        return '/{language}'.format(language=random.choice(self.languages))

    @property
    def summary_params(self):
        summary_id = '{}/'.format(random.choice(self.summary_ids))
        if random.randint(0, 1):
            summary_id += '?as=html'
        return summary_id

    @task(2)
    def start_edit(self):
        self.client.get('{}/wocat/technologies/edit/new/'.format(self.language))
        self.client.get('{}/wocat/approaches/edit/new/'.format(self.language))

    @task(4)
    def login(self):
        self.client.post(
            '{}/accounts/login/'.format(self.language),
            {'username': 'foo', 'password': 'bar', 'csrfmiddlewaretoken': 'eV6ErWp4nkqY5V9eLmBOyS5EBeenTNRU'}
        )

    @task(2)
    def api_list(self):
        self.client.get('{}/api/v2/questionnaires/'.format(self.language))

    @task(10)
    def index(self):
        self.client.get('{}/wocat/'.format(self.language))

    @task(10)
    def index_list(self):
        self.client.get('{}/wocat/list/'.format(self.language))

    @task(5)
    def summary(self):
        self.client.get('{}/summary/{}'.format(self.language, self.summary_params))

    @task(3)
    def user_profile(self):
        self.client.get('{}/accounts/user/{}/'.format(self.language, self.user_id))

    @task(5)
    def approach(self):
        self.client.get('{}/wocat/approaches/view/{}/'.format(self.language, random.choice(self.approaches)))

    @task(5)
    def technology(self):
        self.client.get('{}/wocat/technologies/view/{}/'.format(self.language, random.choice(self.technologies)))

    @task(2)
    def unccd(self):
        self.client.get('{}/unccd/view/{}/'.format(self.language, random.choice(self.unccd)))


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 2000
    max_wait = 7000
