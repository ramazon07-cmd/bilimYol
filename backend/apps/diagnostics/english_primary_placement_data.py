"""RBIS English Placement Tests for grades 1-4.

Sources:
- Placement_Test_Grades_1-2(1).pdf (Test 1, grades 1 and 2)
- Placement_Test_Grades_3-4(1).pdf (Test 2, grades 3 and 4)

Each grade receives the complete 30-question test assigned to its grade band.
"""


def question(number, topic, skills, difficulty, prompt, options, answer, explanation, context=""):
    return {
        "number": number,
        "topic": topic,
        "skills": tuple(skills),
        "difficulty": difficulty,
        "context": context,
        "prompt": prompt,
        "options": tuple(options),
        "answer": answer,
        "explanation": explanation,
    }


TEST_1_PASSAGES = {
    "tom": (
        "Hello! My name is Tom. I am seven years old. I have a cat. "
        "My cat is white. Its name is Snow. I love my cat."
    ),
    "family": (
        "This is my family. My father is a doctor. My mother is a teacher. "
        "I have one brother. His name is Alex. He is five. We live in a big house."
    ),
    "park": (
        "It is Sunday. Lola is in the park. She plays with her ball. "
        "The ball is red and yellow. Her dog Rex runs and jumps. Lola and Rex are happy."
    ),
}

TEST_1_QUESTIONS = [
    question(1, "grammar-foundations", ("grammar-accuracy",), "basic", "I ______ a boy.",
             ("am", "is", "are", "be"), "A", "The subject 'I' takes 'am'."),
    question(2, "grammar-foundations", ("grammar-accuracy",), "basic", "This is ______ apple.",
             ("a", "two", "is", "an"), "D", "A word beginning with a vowel sound takes 'an'."),
    question(3, "grammar-foundations", ("grammar-accuracy",), "basic", "She ______ my friend.",
             ("am", "is", "are", "it"), "B", "The singular subject 'she' takes 'is'."),
    question(4, "grammar-foundations", ("grammar-accuracy",), "basic", "______ name is Aziz.",
             ("I", "Me", "My", "Am"), "C", "The possessive adjective before 'name' is 'my'."),
    question(5, "grammar-foundations", ("grammar-accuracy",), "basic", "They ______ students.",
             ("is", "am", "a", "are"), "D", "The plural subject 'they' takes 'are'."),
    question(6, "grammar-foundations", ("grammar-accuracy",), "basic", "I have two ______.",
             ("cat", "cats", "a cat", "cates"), "B", "After 'two', the regular plural 'cats' is required."),
    question(7, "grammar-foundations", ("question-formation",), "basic", "______ is that? - It is a dog.",
             ("What", "Who", "Where", "How"), "A", "'What' asks about a thing or animal."),
    question(8, "grammar-foundations", ("grammar-accuracy",), "basic", "The ball is ______ the box.",
             ("an", "is", "in", "am"), "C", "'In' shows that the ball is inside the box."),
    question(9, "grammar-foundations", ("question-formation",), "basic", "______ you like ice cream? - Yes, I do.",
             ("Is", "Are", "Am", "Do"), "D", "Present simple questions with 'you' use 'do'."),
    question(10, "grammar-foundations", ("grammar-accuracy",), "basic", "Look! It is ______ elephant.",
             ("a", "an", "two", "the a"), "B", "'Elephant' begins with a vowel sound, so use 'an'."),
    question(11, "grammar-foundations", ("grammar-accuracy",), "medium", "He ______ got a red car.",
             ("have", "is", "are", "has"), "D", "The singular subject 'he' takes 'has got'."),
    question(12, "tense-and-voice", ("tense-control",), "medium", "Look! The cat ______ now.",
             ("is sleeping", "sleep", "sleeps", "sleeping"), "A", "An action happening now uses the present continuous."),
    question(13, "tense-and-voice", ("tense-control",), "medium", "Yesterday we ______ to the park.",
             ("go", "goes", "went", "going"), "C", "'Yesterday' requires the past simple form 'went'."),
    question(14, "grammar-foundations", ("grammar-accuracy",), "medium", "This is my sister. ______ name is Malika.",
             ("His", "My", "It", "Her"), "D", "The possessive adjective for a girl or woman is 'her'."),
    question(15, "grammar-foundations", ("grammar-accuracy",), "medium", "An elephant is ______ than a cat.",
             ("big", "bigger", "biggest", "more big"), "B", "The comparative form of 'big' is 'bigger'."),
    question(16, "reading-narrative", ("factual-reading",), "basic", "What is the boy's name?",
             ("Snow", "Tom", "Cat", "White"), "B", "The passage says, 'My name is Tom.'", TEST_1_PASSAGES["tom"]),
    question(17, "reading-narrative", ("factual-reading",), "basic", "How old is Tom?",
             ("six", "eight", "nine", "seven"), "D", "Tom says that he is seven years old.", TEST_1_PASSAGES["tom"]),
    question(18, "reading-narrative", ("factual-reading",), "basic", "What pet does Tom have?",
             ("a dog", "a bird", "a cat", "a fish"), "C", "Tom says that he has a cat.", TEST_1_PASSAGES["tom"]),
    question(19, "reading-narrative", ("factual-reading",), "basic", "What colour is the cat?",
             ("white", "black", "brown", "red"), "A", "The passage says the cat is white.", TEST_1_PASSAGES["tom"]),
    question(20, "reading-narrative", ("factual-reading",), "basic", "What is the cat's name?",
             ("Tom", "White", "Kitty", "Snow"), "D", "The cat's name is Snow.", TEST_1_PASSAGES["tom"]),
    question(21, "reading-narrative", ("factual-reading",), "basic", "What is the father's job?",
             ("a teacher", "a doctor", "a driver", "a cook"), "B", "The passage says the father is a doctor.", TEST_1_PASSAGES["family"]),
    question(22, "reading-narrative", ("factual-reading",), "basic", "Who is a teacher?",
             ("the father", "the brother", "the mother", "Alex"), "C", "The mother is a teacher.", TEST_1_PASSAGES["family"]),
    question(23, "reading-narrative", ("factual-reading",), "basic", "What is the brother's name?",
             ("Alex", "Tom", "Aziz", "Sam"), "A", "The passage says the brother's name is Alex.", TEST_1_PASSAGES["family"]),
    question(24, "reading-narrative", ("factual-reading",), "basic", "How old is the brother?",
             ("four", "five", "six", "seven"), "B", "Alex is five years old.", TEST_1_PASSAGES["family"]),
    question(25, "reading-narrative", ("factual-reading",), "basic", "Where do they live?",
             ("in a small house", "in a school", "in a car", "in a big house"), "D", "They live in a big house.", TEST_1_PASSAGES["family"]),
    question(26, "reading-narrative", ("factual-reading",), "basic", "What day is it?",
             ("Monday", "Friday", "Sunday", "Saturday"), "C", "The first sentence says it is Sunday.", TEST_1_PASSAGES["park"]),
    question(27, "reading-narrative", ("factual-reading",), "basic", "Where is Lola?",
             ("at school", "at home", "in a shop", "in the park"), "D", "Lola is in the park.", TEST_1_PASSAGES["park"]),
    question(28, "reading-narrative", ("factual-reading",), "basic", "What does Lola play with?",
             ("a ball", "a car", "a doll", "a kite"), "A", "The passage says she plays with her ball.", TEST_1_PASSAGES["park"]),
    question(29, "reading-narrative", ("factual-reading",), "basic", "What colours is the ball?",
             ("red and blue", "red and yellow", "green and yellow", "blue and white"), "B", "The ball is red and yellow.", TEST_1_PASSAGES["park"]),
    question(30, "reading-narrative", ("factual-reading",), "basic", "What is the dog's name?",
             ("Max", "Snow", "Rex", "Lola"), "C", "The dog's name is Rex.", TEST_1_PASSAGES["park"]),
]


TEST_2_PASSAGES = {
    "school-day": (
        "My name is Kamila and I am nine years old. I get up at seven o'clock every morning. "
        "I have breakfast with my family and then I walk to school with my best friend Nodira. "
        "School starts at half past eight. My favourite subject is Maths because I like numbers. "
        "After school, I do my homework and then I play in the yard."
    ),
    "mountains": (
        "Last Sunday, Timur and his family went to the mountains. They left home early in the morning "
        "and travelled by car for two hours. First, they walked along a small river. Then they had a "
        "picnic under a big tree. Timur's mother made sandwiches and his father brought fruit and juice. "
        "In the afternoon, it started to rain, so they went back to the car. Timur was tired but very happy."
    ),
    "pandas": (
        "Pandas are big black and white animals. They live in the mountains of China. Pandas eat bamboo "
        "for many hours every day. A baby panda is very small - it is smaller than a cup of tea! Pandas can "
        "climb trees very well, but they cannot run fast. Many people around the world love pandas, and zoos "
        "are helping to keep these beautiful animals safe."
    ),
}

TEST_2_QUESTIONS = [
    question(1, "grammar-foundations", ("grammar-accuracy",), "basic", "My brother ______ football every Saturday.",
             ("play", "plays", "playing", "is play"), "B", "A third-person singular subject takes 'plays'."),
    question(2, "tense-and-voice", ("tense-control",), "basic", "Look! The children ______ in the garden.",
             ("play", "plays", "are playing", "played"), "C", "'Look!' signals an action happening now, so use the present continuous."),
    question(3, "grammar-foundations", ("grammar-accuracy",), "basic", "There ______ some milk in the fridge.",
             ("is", "are", "am", "have"), "A", "'Milk' is uncountable and singular, so use 'is'."),
    question(4, "grammar-foundations", ("question-formation",), "basic", "______ there any apples on the table?",
             ("Is", "Are", "Am", "Do"), "B", "Plural 'apples' requires 'Are there...?'."),
    question(5, "grammar-foundations", ("grammar-accuracy",), "basic", "She ______ like bananas.",
             ("don't", "isn't", "doesn't", "aren't"), "C", "The negative present simple with 'she' uses 'doesn't'."),
    question(6, "grammar-foundations", ("grammar-accuracy",), "basic", "We go to school ______ bus.",
             ("on", "in", "by", "at"), "C", "The standard transport phrase is 'by bus'."),
    question(7, "grammar-foundations", ("grammar-accuracy",), "medium", "This book is ______ than that one.",
             ("interesting", "more interesting", "most interesting", "interestinger"), "B", "Long adjectives form the comparative with 'more'."),
    question(8, "tense-and-voice", ("tense-control",), "basic", "Yesterday I ______ to the zoo with my family.",
             ("go", "goes", "went", "going"), "C", "'Yesterday' requires the past simple form 'went'."),
    question(9, "grammar-foundations", ("grammar-accuracy",), "basic", "Can you swim? - Yes, I ______.",
             ("can", "am", "do", "swim"), "A", "A short answer to a 'can' question repeats 'can'."),
    question(10, "grammar-foundations", ("grammar-accuracy",), "basic", "My birthday is ______ May.",
             ("at", "on", "in", "by"), "C", "Months take the preposition 'in'."),
    question(11, "grammar-foundations", ("question-formation",), "medium", "______ pens are these? - They are Aziza's.",
             ("Who", "Whose", "What", "Which"), "B", "'Whose' asks about possession."),
    question(12, "grammar-foundations", ("grammar-accuracy",), "basic", "He gets up ______ seven o'clock.",
             ("in", "on", "at", "by"), "C", "Clock times take the preposition 'at'."),
    question(13, "grammar-foundations", ("grammar-accuracy",), "basic", "There aren't ______ chairs in the room.",
             ("some", "any", "a", "an"), "B", "Negative plural statements normally use 'any'."),
    question(14, "grammar-foundations", ("grammar-accuracy",), "medium", "Dilshod is the ______ boy in our class.",
             ("tall", "taller", "tallest", "most tall"), "C", "A comparison with the whole class uses the superlative 'tallest'."),
    question(15, "tense-and-voice", ("tense-control",), "medium", "They ______ watch TV last night.",
             ("don't", "doesn't", "didn't", "aren't"), "C", "A negative past simple sentence uses 'didn't'."),
    question(16, "reading-narrative", ("factual-reading",), "basic", "How old is Kamila?",
             ("seven", "eight", "nine", "ten"), "C", "Kamila says that she is nine years old.", TEST_2_PASSAGES["school-day"]),
    question(17, "reading-narrative", ("factual-reading",), "basic", "How does Kamila go to school?",
             ("by bus", "by car", "on foot", "by bike"), "C", "She walks to school, which means she goes on foot.", TEST_2_PASSAGES["school-day"]),
    question(18, "reading-narrative", ("factual-reading",), "basic", "What time does school start?",
             ("7:00", "7:30", "8:00", "8:30"), "D", "Half past eight is 8:30.", TEST_2_PASSAGES["school-day"]),
    question(19, "reading-narrative", ("factual-reading",), "basic", "Why does Kamila like Maths?",
             ("She likes reading", "She likes numbers", "Her friend likes it", "It is easy"), "B", "The passage says she likes Maths because she likes numbers.", TEST_2_PASSAGES["school-day"]),
    question(20, "reading-narrative", ("factual-reading",), "basic", "What does Kamila do first after school?",
             ("plays in the yard", "watches TV", "does her homework", "has breakfast"), "C", "She does her homework before playing in the yard.", TEST_2_PASSAGES["school-day"]),
    question(21, "reading-narrative", ("factual-reading",), "basic", "When did the family go to the mountains?",
             ("last Saturday", "last Sunday", "yesterday", "last month"), "B", "The passage begins with 'Last Sunday'.", TEST_2_PASSAGES["mountains"]),
    question(22, "reading-narrative", ("factual-reading",), "basic", "How long was the journey by car?",
             ("one hour", "two hours", "three hours", "half an hour"), "B", "They travelled by car for two hours.", TEST_2_PASSAGES["mountains"]),
    question(23, "reading-narrative", ("factual-reading",), "basic", "Where did they have a picnic?",
             ("by the car", "near a shop", "under a big tree", "in a cafe"), "C", "They had a picnic under a big tree.", TEST_2_PASSAGES["mountains"]),
    question(24, "reading-narrative", ("factual-reading",), "basic", "Who made the sandwiches?",
             ("Timur", "his father", "his mother", "his sister"), "C", "Timur's mother made the sandwiches.", TEST_2_PASSAGES["mountains"]),
    question(25, "reading-narrative", ("factual-reading",), "basic", "Why did they go back to the car?",
             ("They were hungry", "It started to rain", "It was dark", "Timur was ill"), "B", "They returned because it started to rain.", TEST_2_PASSAGES["mountains"]),
    question(26, "reading-narrative", ("factual-reading",), "basic", "Where do pandas live?",
             ("in Africa", "in China", "in America", "in India"), "B", "The passage says pandas live in the mountains of China.", TEST_2_PASSAGES["pandas"]),
    question(27, "reading-narrative", ("factual-reading",), "basic", "What do pandas eat?",
             ("fish", "meat", "bamboo", "fruit"), "C", "Pandas eat bamboo.", TEST_2_PASSAGES["pandas"]),
    question(28, "reading-narrative", ("factual-reading",), "basic", "What is true about a baby panda?",
             ("It is very big", "It is very small", "It can run fast", "It is brown"), "B", "The passage says a baby panda is very small.", TEST_2_PASSAGES["pandas"]),
    question(29, "reading-narrative", ("factual-reading",), "basic", "What can pandas do well?",
             ("run fast", "swim", "climb trees", "jump high"), "C", "Pandas can climb trees very well.", TEST_2_PASSAGES["pandas"]),
    question(30, "reading-narrative", ("factual-reading",), "basic", "Who is helping to keep pandas safe?",
             ("zoos", "schools", "shops", "farmers"), "A", "The passage says zoos are helping to keep pandas safe.", TEST_2_PASSAGES["pandas"]),
]


PRIMARY_TESTS = {
    "PT1": {
        "grades": (1, 2),
        "duration_minutes": 30,
        "source_name": "Placement_Test_Grades_1-2(1).pdf",
        "level_range": "Pre-A1-A2",
        "questions": TEST_1_QUESTIONS,
    },
    "PT2": {
        "grades": (3, 4),
        "duration_minutes": 40,
        "source_name": "Placement_Test_Grades_3-4(1).pdf",
        "level_range": "Pre-A1-A2",
        "questions": TEST_2_QUESTIONS,
    },
}


def validate_data():
    for test_code, spec in PRIMARY_TESTS.items():
        questions = spec["questions"]
        numbers = [item["number"] for item in questions]
        if numbers != list(range(1, 31)):
            raise ValueError(f"{test_code}: savollar 1-30 tartibida bo‘lishi kerak.")
        for item in questions:
            if len(item["options"]) != 4:
                raise ValueError(f"{test_code}-{item['number']}: aynan 4 ta variant kerak.")
            if item["answer"] not in {"A", "B", "C", "D"}:
                raise ValueError(f"{test_code}-{item['number']}: javob kaliti noto‘g‘ri.")


validate_data()
