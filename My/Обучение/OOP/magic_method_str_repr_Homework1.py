class Person:

    def __init__(self, name, surname, gender='male'):
        self.name = name
        self.surname = surname
        self.gender = gender

    def get_gender(self):
        return self.gender

    def set_gender(self, gender):
        if gender != 'female':
            print("Я не знаю, что Вы имели в виду. Пусть это будет мальчик.")
            self.gender = 'male'
        else:
            self.gender = 'female'

    def __str__(self):
        if self.gender == 'female':
            return f"Гражданка {self.name} {self.surname}"
        else:
            return f"Гражданин {self.name} {self.surname}"


p1 = Person("Chuck", "Norris")
print(p1)
p2 = Person("Mila", "Kunis")
p2.set_gender("female")
print(p2)
p3 = Person("Оби-Ван", "Кеноби")
p3.set_gender("True")
print(p3)
