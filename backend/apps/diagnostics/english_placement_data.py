"""RBIS English Placement Test 3 data.

The source is the school-provided "Placement Test Grades 5-11" document.
Questions are stored once and combined into grade-specific 20-question exams.
"""

TOPIC_SPECS = {
    "grammar-foundations": {
        "code": "ENG-GRAM-FOUND",
        "title": "Grammar foundations",
        "order": 1,
        "healthy_threshold": 75,
    },
    "tense-and-voice": {
        "code": "ENG-TENSE-VOICE",
        "title": "Tense, aspect and voice",
        "order": 2,
        "healthy_threshold": 70,
    },
    "advanced-syntax": {
        "code": "ENG-ADV-SYNTAX",
        "title": "Advanced sentence structure",
        "order": 3,
        "healthy_threshold": 65,
    },
    "reading-narrative": {
        "code": "ENG-READ-NARR",
        "title": "Reading: personal narrative",
        "order": 4,
        "healthy_threshold": 75,
    },
    "reading-culture": {
        "code": "ENG-READ-CULT",
        "title": "Reading: history and culture",
        "order": 5,
        "healthy_threshold": 70,
    },
    "critical-reading": {
        "code": "ENG-READ-CRIT",
        "title": "Critical reading",
        "order": 6,
        "healthy_threshold": 65,
    },
}

SKILL_SPECS = {
    "grammar-accuracy": ("Grammar accuracy", 1),
    "question-formation": ("Question formation", 2),
    "tense-control": ("Tense and aspect control", 3),
    "sentence-transformation": ("Sentence transformation", 4),
    "advanced-syntax": ("Advanced syntax", 5),
    "factual-reading": ("Reading for explicit detail", 6),
    "inference": ("Inference", 7),
    "main-idea": ("Main idea and summary", 8),
    "vocabulary-context": ("Vocabulary in context", 9),
    "critical-reading": ("Critical reading and author purpose", 10),
}

PASSAGES = {
    "new-hobby": (
        "Six months ago, Jasur started learning to play the guitar. At first, it was "
        "very difficult, and his fingers hurt after every lesson. He wanted to give up, "
        "but his teacher told him to practise for just fifteen minutes every day instead "
        "of one long lesson a week. This small change helped a lot. Now Jasur can play "
        "five songs, and last week he played in front of his classmates for the first "
        "time. He was nervous, but everyone clapped at the end."
    ),
    "silk-road": (
        "The Silk Road was not a single road but a network of trade routes that connected "
        "China with Central Asia, the Middle East and Europe for more than 1,500 years. "
        "Merchants transported silk, spices, glass and precious stones across deserts and "
        "mountains. However, goods were not the only things that travelled along these "
        "routes. Ideas, religions, languages and inventions such as paper also spread from "
        "one region to another. Cities along the way, including Samarkand and Bukhara, "
        "became rich and famous centres of culture and science. Although sea routes later "
        "replaced much of this land trade, the influence of the Silk Road can still be "
        "seen in the region today."
    ),
    "choice": (
        "Conventional wisdom holds that the more options we have, the better off we are; "
        "choice, after all, is widely regarded as the currency of freedom. Yet a growing "
        "body of psychological research suggests that beyond a certain point, abundance "
        "becomes a burden. Faced with dozens of near-identical products, consumers "
        "frequently postpone the decision altogether or, having finally chosen, are "
        "haunted by the suspicion that a rejected alternative might have served them "
        "better. This phenomenon, sometimes termed 'choice overload', does not imply that "
        "options should be ruthlessly stripped away - few of us would trade a supermarket "
        "for a ration book. Rather, it points to the value of thoughtful curation: "
        "presenting people with a manageable range of meaningfully distinct alternatives, "
        "so that deciding feels like an act of self-expression rather than a source of "
        "quiet anxiety."
    ),
}


def question(
    number,
    topic,
    skills,
    difficulty,
    prompt,
    options,
    answer,
    explanation,
    passage=None,
):
    return {
        "number": number,
        "topic": topic,
        "skills": skills,
        "difficulty": difficulty,
        "context": PASSAGES.get(passage, ""),
        "prompt": prompt,
        "options": options,
        "answer": answer,
        "explanation": explanation,
    }


QUESTIONS = [
    question(
        1, "grammar-foundations", ("grammar-accuracy",), "basic",
        "She ______ a doctor.",
        ("is", "am", "are", "be"), "A",
        "'She' takes the singular form 'is'.",
    ),
    question(
        2, "grammar-foundations", ("grammar-accuracy",), "basic",
        "I ______ two brothers.",
        ("has", "is", "am", "have"), "D",
        "The subject 'I' takes the base verb 'have'.",
    ),
    question(
        3, "grammar-foundations", ("question-formation",), "basic",
        "______ you like pizza? - Yes, I do.",
        ("Is", "Are", "Do", "Does"), "C",
        "Present simple questions with 'you' use the auxiliary 'do'.",
    ),
    question(
        4, "grammar-foundations", ("tense-control",), "basic",
        "We ______ to the seaside last summer.",
        ("go", "went", "goes", "gone"), "B",
        "A finished past time requires the past simple form 'went'.",
    ),
    question(
        5, "grammar-foundations", ("grammar-accuracy",), "basic",
        "My brother is ______ than me.",
        ("tall", "tallest", "more tall", "taller"), "D",
        "A short adjective forms the comparative with '-er': 'taller'.",
    ),
    question(
        6, "grammar-foundations", ("grammar-accuracy",), "basic",
        "There isn't ______ milk in the fridge.",
        ("much", "many", "a few", "some"), "A",
        "'Milk' is uncountable, so a negative sentence uses 'much'.",
    ),
    question(
        7, "tense-and-voice", ("tense-control",), "medium",
        "I ______ English since 2021.",
        ("learn", "have been learning", "am learning", "learned"), "B",
        "An activity continuing from a past point until now uses the present perfect continuous.",
    ),
    question(
        8, "tense-and-voice", ("tense-control", "sentence-transformation"), "medium",
        "If it rains tomorrow, we ______ at home.",
        ("stay", "stayed", "will stay", "would stay"), "C",
        "The first conditional uses present simple after 'if' and 'will' in the result clause.",
    ),
    question(
        9, "tense-and-voice", ("sentence-transformation",), "medium",
        "This bridge ______ over a hundred years ago.",
        ("built", "is built", "has built", "was built"), "D",
        "The bridge receives the action in the past, so the past passive is required.",
    ),
    question(
        10, "tense-and-voice", ("tense-control",), "medium",
        "By the time we arrived, the film ______.",
        ("had already started", "already started", "has already started", "was already starting"), "A",
        "The film started before another past action, so the past perfect is used.",
    ),
    question(
        11, "tense-and-voice", ("grammar-accuracy",), "medium",
        "I'm not used ______ up early on weekends.",
        ("to get", "getting", "get", "to getting"), "D",
        "The pattern is 'be used to' followed by a noun or gerund.",
    ),
    question(
        12, "tense-and-voice", ("sentence-transformation",), "medium",
        "He asked me where ______.",
        ("do I live", "I lived", "I live", "did I live"), "B",
        "Reported questions use statement word order and a backshifted tense.",
    ),
    question(
        13, "advanced-syntax", ("advanced-syntax",), "high",
        "Hardly ______ the house when it started to snow.",
        ("had I left", "I had left", "I left", "did I leave"), "A",
        "After negative 'hardly', formal English uses inversion: 'had I left'.",
    ),
    question(
        14, "advanced-syntax", ("advanced-syntax", "sentence-transformation"), "high",
        "______ the weather been better, we would have gone hiking.",
        ("If", "Should", "Had", "Were"), "C",
        "'Had the weather been better' is the inverted form of a third conditional.",
    ),
    question(
        15, "advanced-syntax", ("advanced-syntax",), "high",
        "It was only when the results came out ______ she realised her mistake.",
        ("when", "that", "which", "what"), "B",
        "The emphatic cleft structure is 'It was ... that ...'.",
    ),
    question(
        16, "reading-narrative", ("factual-reading",), "basic",
        "How long has Jasur been playing the guitar?",
        ("about half a year", "just over a year", "a few weeks", "five years"), "A",
        "The passage says that Jasur started six months ago.",
        "new-hobby",
    ),
    question(
        17, "reading-narrative", ("inference",), "basic",
        "Why did Jasur almost stop playing?",
        ("his teacher was unkind", "lessons were too expensive", "he had no free time", "the beginning was painful and difficult"), "D",
        "His fingers hurt and the activity felt difficult at first.",
        "new-hobby",
    ),
    question(
        18, "reading-narrative", ("factual-reading",), "basic",
        "What change did the teacher suggest?",
        ("shorter but more frequent practice", "longer weekly lessons", "taking a break from music", "changing to another instrument"), "A",
        "The teacher suggested fifteen minutes every day instead of one long weekly lesson.",
        "new-hobby",
    ),
    question(
        19, "reading-narrative", ("factual-reading",), "basic",
        "What happened at the end of Jasur's first performance?",
        ("he forgot the songs", "the audience showed they liked it", "the teacher stopped him", "nobody was listening"), "B",
        "His classmates clapped, showing a positive response.",
        "new-hobby",
    ),
    question(
        20, "reading-narrative", ("main-idea", "inference"), "basic",
        "How can we best describe Jasur's progress?",
        ("He gave up quickly", "He learned without any help", "He improved through regular short practice", "He still cannot play any songs"), "C",
        "The passage links his improvement to short, regular practice.",
        "new-hobby",
    ),
    question(
        21, "reading-culture", ("main-idea",), "medium",
        "What common belief about the Silk Road does the text correct?",
        ("that it was a single route", "that it carried silk", "that it reached Europe", "that it crossed deserts"), "A",
        "The opening sentence explains that it was a network, not one road.",
        "silk-road",
    ),
    question(
        22, "reading-culture", ("factual-reading",), "medium",
        "Besides trade goods, what else moved along the routes?",
        ("armies and weapons", "knowledge and beliefs", "tourists and students", "wild animals"), "B",
        "The text names ideas, religions, languages and inventions.",
        "silk-road",
    ),
    question(
        23, "reading-culture", ("inference",), "medium",
        "What effect did the routes have on cities such as Samarkand?",
        ("They lost their importance", "They were often attacked", "They stopped trading", "They grew wealthy and influential"), "D",
        "The cities became rich and famous centres of culture and science.",
        "silk-road",
    ),
    question(
        24, "reading-culture", ("factual-reading",), "medium",
        "According to the text, why did the land routes decline?",
        ("Traders began to prefer travel by water", "The deserts became too dangerous", "The cities became too expensive", "Paper was no longer needed"), "A",
        "Sea routes later replaced much of the land trade.",
        "silk-road",
    ),
    question(
        25, "reading-culture", ("main-idea",), "medium",
        "What is the writer's main point in the final sentence?",
        ("The Silk Road has been completely forgotten", "Its legacy remains visible in the region", "Sea trade is no longer important", "China stopped trading with Europe"), "B",
        "The final sentence states that the Silk Road's influence can still be seen.",
        "silk-road",
    ),
    question(
        26, "critical-reading", ("main-idea", "critical-reading"), "high",
        "According to 'conventional wisdom', what is true about choice?",
        ("Fewer options are always better", "Choice is unimportant to freedom", "More choice makes people better off", "People dislike having options"), "C",
        "The opening claim says that more options are commonly believed to improve life.",
        "choice",
    ),
    question(
        27, "critical-reading", ("factual-reading",), "high",
        "What do consumers often do when faced with too many similar options?",
        ("They delay making a decision", "They always buy the cheapest one", "They ask the seller to choose", "They buy several products at once"), "A",
        "The passage says that consumers frequently postpone the decision.",
        "choice",
    ),
    question(
        28, "critical-reading", ("vocabulary-context", "inference"), "high",
        "The phrase 'haunted by the suspicion' suggests that, after choosing, people feel ______.",
        ("relief", "pride", "excitement", "lingering doubt"), "D",
        "The phrase describes continuing uncertainty about the rejected alternatives.",
        "choice",
    ),
    question(
        29, "critical-reading", ("critical-reading", "inference"), "high",
        "What point does the writer make with the example of 'a ration book'?",
        ("Everyone wants fewer shops", "Few people would accept extreme restriction", "Ration books were popular in the past", "Supermarkets offer too little choice"), "B",
        "The contrast rejects removing choice so severely that freedom disappears.",
        "choice",
    ),
    question(
        30, "critical-reading", ("main-idea", "critical-reading"), "high",
        "Which solution does the writer appear to favour?",
        ("removing all unnecessary options", "offering unlimited variety", "a smaller, well-chosen range of options", "letting experts decide for consumers"), "C",
        "The writer supports thoughtful curation and a manageable range of distinct choices.",
        "choice",
    ),
]


GRADE_QUESTION_NUMBERS = {
    5: tuple(range(1, 11)) + tuple(range(16, 26)),
    6: tuple(range(2, 13)) + tuple(range(16, 25)),
    7: tuple(range(4, 14)) + tuple(range(16, 26)),
    8: tuple(range(6, 16)) + tuple(range(16, 26)),
    9: tuple(range(7, 16)) + (20,) + tuple(range(21, 31)),
    10: tuple(range(9, 16)) + tuple(range(18, 31)),
    11: tuple(range(10, 16)) + tuple(range(17, 31)),
}

GRADE_LEVELS = {
    5: "A1-A2",
    6: "A2",
    7: "A2-B1",
    8: "B1",
    9: "B1-B2",
    10: "B2",
    11: "B2-C1",
}


def grade_bounds(question_number):
    grades = [
        grade
        for grade, question_numbers in GRADE_QUESTION_NUMBERS.items()
        if question_number in question_numbers
    ]
    return min(grades), max(grades)


def validate_data():
    numbers = [item["number"] for item in QUESTIONS]
    if numbers != list(range(1, 31)):
        raise ValueError("English placement savollari 1-30 tartibida bo‘lishi kerak.")
    for grade, question_numbers in GRADE_QUESTION_NUMBERS.items():
        if len(question_numbers) != 20 or len(set(question_numbers)) != 20:
            raise ValueError(f"{grade}-sinf testida aynan 20 ta noyob savol bo‘lishi kerak.")
        if not set(question_numbers).issubset(numbers):
            raise ValueError(f"{grade}-sinf testida noma’lum savol raqami bor.")
    for item in QUESTIONS:
        if item["answer"] not in {"A", "B", "C", "D"}:
            raise ValueError(f"{item['number']}-savol javobi noto‘g‘ri.")
        if len(item["options"]) != 4:
            raise ValueError(f"{item['number']}-savolda aynan 4 ta variant bo‘lishi kerak.")


validate_data()
