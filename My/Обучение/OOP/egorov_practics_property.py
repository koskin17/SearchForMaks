# Практика по property
class User:

    def __int__(self, login, password):
        self.login = login
        self.password = password


# Проблема, которая возникает при работе с классом в том, что можно спокойно обращаться к аттрибутам этого
# класса, менять аттрибуты и т.д.
# В данном случае в аттрибут password можно сохранить всё, что угодно

q = User("Ivan")
