from faker import Faker

def generate_username(locale='en_US'):
    faker = Faker(locale)
    return faker.user_name()