import random

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.topics.models import Topic, Subtopic, ProblemType, Formula
from backend.apps.questions.models import Question, SolutionStep, Shortcut
from backend.apps.users.models import User


class Command(BaseCommand):
    help = "Seed development learning content: topics, subtopics, problem types, formulas, questions, solutions, shortcuts."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Seeding learning content...")
            user = self._ensure_user()
            topics = self._seed_topics()
            self._seed_subtopics(topics)
            self._seed_problem_types(topics)
            self._seed_formulas(topics)
            self._seed_questions(topics, user)
        self.stdout.write(self.style.SUCCESS("Learning content seeded successfully."))

    def _ensure_user(self):
        user, _ = User.objects.get_or_create(
            email="seeduser@example.com",
            defaults={
                "username": "seeduser",
                "password": "pbkdf2_sha256$600000$dummy$dummy",
            },
        )
        return user

    def _seed_topics(self):
        data = [
            ("Number System", "number-system", "Covers basics of numbers, divisibility, remainders, and number series."),
            ("HCF & LCM", "hcf-lcm", "Learn to find highest common factors and least common multiples efficiently."),
            ("Percentage", "percentage", "Master percentage calculations, increases, decreases, and applications."),
            ("Profit & Loss", "profit-loss", "Understand profit percent, loss percent, and successive transactions."),
            ("Ratio & Proportion", "ratio-proportion", "Study ratios, proportions, and their real-world applications."),
            ("Average", "average", "Learn arithmetic mean, weighted average, and average speed problems."),
            ("Ages", "ages", "Solve age relationship problems using algebraic equations."),
            ("Simple Interest", "simple-interest", "Calculate simple interest, amount, and related time-value problems."),
            ("Compound Interest", "compound-interest", "Master compound interest, effective rates, and instalment problems."),
            ("Time & Work", "time-work", "Calculate work done by individuals and groups over time."),
            ("Pipes & Cisterns", "pipes-cisterns", "Solve inlet and outlet pipe problems with varying rates."),
            ("Time Speed Distance", "time-speed-distance", "Master relations between time, speed, and distance."),
            ("Problems on Trains", "problems-trains", "Solve train-related problems involving relative speed and crossing."),
            ("Probability", "probability", "Study basic probability, dice, coins, and card problems."),
            ("Permutation & Combination", "permutation-combination", "Learn counting principles, permutations, and combinations."),
            ("Mixtures & Allegations", "mixtures-allegations", "Solve mixture ratio problems using the allegation method."),
            ("Data Interpretation", "data-interpretation", "Interpret tables, charts, and graphs for data analysis."),
        ]
        topics = {}
        for name, slug, description in data:
            topic, _ = Topic.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description, "order": len(topics) + 1},
            )
            topics[slug] = topic
        return topics

    def _seed_subtopics(self, topics):
        mapping = {
            "percentage": ["Basic Percentage", "Percentage Change", "Successive Percentage"],
            "profit-loss": ["Profit Percent", "Loss Percent", "Successive Profit/Loss"],
            "average": ["Arithmetic Mean", "Weighted Average", "Average Speed"],
            "simple-interest": ["SI Basics", "Instalments"],
            "compound-interest": ["CI Basics", "Effective Rate", "Instalments"],
            "time-work": ["Work and Efficiency", "Groups Working Together"],
            "probability": ["Coins and Dice", "Cards", "Miscellaneous"],
            "permutation-combination": ["Permutations", "Combinations", "Selection Problems"],
            "data-interpretation": ["Tables", "Charts and Graphs", "DI Caselets"],
        }
        for topic_slug, subtopic_names in mapping.items():
            topic = topics[topic_slug]
            for idx, name in enumerate(subtopic_names):
                Subtopic.objects.get_or_create(
                    topic=topic,
                    name=name,
                    defaults={"description": f"{name} under {topic.name}.", "order": idx + 1},
                )

    def _seed_problem_types(self, topics):
        types = [
            ("percentage", "Finding Percentage", "Find x% of a given quantity."),
            ("percentage", "Percentage Increase/Decrease", "Calculate percentage change between two values."),
            ("percentage", "Successive Percentage", "Apply successive percentage changes."),
            ("profit-loss", "Profit/Loss Percent", "Calculate profit or loss percentage."),
            ("profit-loss", "Successive Profit/Loss", "Find overall profit/loss across successive transactions."),
            ("ratio-proportion", "Combining Ratios", "Combine two ratios sharing a common term."),
            ("ratio-proportion", "Ratio Division", "Divide a quantity in a given ratio."),
            ("average", "Simple Average", "Compute arithmetic mean of given values."),
            ("average", "Weighted Average", "Compute weighted average when values have different weights."),
            ("average", "Average Speed", "Find average speed over multiple legs of a journey."),
            ("ages", "Age Problems", "Solve problems involving present and future ages."),
            ("simple-interest", "SI Calculation", "Calculate simple interest and amount."),
            ("simple-interest", "Instalment Problems", "Solve problems with equal instalments."),
            ("compound-interest", "CI Calculation", "Calculate compound interest and amount."),
            ("compound-interest", "Effective Rate", "Find effective annual interest rate."),
            ("time-work", "Work Done Together", "Calculate time when multiple workers collaborate."),
            ("time-work", "Men and Days", "Use inverse proportion to find workers or days."),
            ("pipes-cisterns", "Filling and Emptying", "Find net time when inlet and outlet pipes operate together."),
            ("time-speed-distance", "Basic TSD", "Apply distance = speed × time."),
            ("time-speed-distance", "Relative Speed", "Use relative speed for trains and crossing problems."),
            ("time-speed-distance", "Average Speed", "Find average speed over multiple legs."),
            ("problems-trains", "Train Crossing", "Solve problems involving trains crossing poles or other trains."),
            ("probability", "Basic Probability", "Find probability of simple events."),
            ("probability", "Combinations Probability", "Use combinations for probability of selections."),
            ("permutation-combination", "Arrangements", "Count possible arrangements of items."),
            ("permutation-combination", "Selections", "Count possible selections of items."),
            ("mixtures-allegations", "Mixture Problems", "Solve mixture ratio problems."),
            ("number-system", "Number Properties", "Solve problems involving divisibility and remainders."),
            ("number-system", "Series and Sums", "Find sums of number series."),
            ("number-system", "Unit Digit", "Find unit digit of large powers."),
            ("hcf-lcm", "HCF/LCM Basics", "Find highest common factors and least common multiples."),
            ("hcf-lcm", "Product Relation", "Use HCF * LCM = Product of numbers."),
            ("data-interpretation", "Table Analysis", "Answer questions using tabular data."),
            ("data-interpretation", "Graph Analysis", "Answer questions using bar, line, or pie charts."),
        ]
        for topic_slug, name, description in types:
            topic = topics[topic_slug]
            ProblemType.objects.get_or_create(
                topic=topic,
                name=name,
                defaults={"description": description, "is_active": True},
            )

    def _seed_formulas(self, topics):
        formulas = [
            ("percentage", "Percentage Formula", "Percentage = (Part / Whole) × 100", "Calculate what percent a part is of the whole."),
            ("percentage", "Percentage Change", "Change % = ((New - Old) / Old) × 100", "Calculate percentage increase or decrease."),
            ("profit-loss", "Profit Percent", "Profit % = (Profit / CP) × 100", "Calculate profit percentage from cost and selling price."),
            ("profit-loss", "Loss Percent", "Loss % = (Loss / CP) × 100", "Calculate loss percentage from cost and selling price."),
            ("average", "Arithmetic Mean", "Average = Sum / Count", "Find the simple arithmetic mean."),
            ("average", "Weighted Average", "WA = (Sum(w_i * x_i)) / (Sum w_i)", "Compute weighted average with weights."),
            ("simple-interest", "Simple Interest", "SI = (P * R * T) / 100", "Calculate simple interest."),
            ("simple-interest", "Amount", "A = P + SI", "Calculate total amount after interest."),
            ("compound-interest", "Compound Interest", "CI = P * ((1 + R/100)^T - 1)", "Calculate compound interest."),
            ("compound-interest", "Effective Rate", "EIR = ((1 + R/n)^n - 1) * 100", "Find effective annual interest rate."),
            ("time-work", "Work", "Work = Efficiency × Time", "Relate work, efficiency, and time."),
            ("time-speed-distance", "Distance", "Distance = Speed × Time", "Basic TSD relation."),
            ("time-speed-distance", "Relative Speed", "Relative Speed = Sum of speeds (opposite direction)", "Use when two objects move toward or away from each other."),
            ("probability", "Probability", "P(E) = Favorable Outcomes / Total Outcomes", "Find probability of an event."),
            ("permutation-combination", "Permutation", "P(n, r) = n! / (n-r)!", "Count ordered arrangements."),
            ("permutation-combination", "Combination", "C(n, r) = n! / (r! * (n-r)!)", "Count unordered selections."),
            ("data-interpretation", "Percentage Share", "Share % = (Part / Total) × 100", "Find percentage share from data."),
        ]
        for topic_slug, name, expr, description in formulas:
            topic = topics[topic_slug]
            pt_name = name.split(" ")[0]
            problem_type = ProblemType.objects.filter(topic=topic, name__icontains=pt_name).first()
            if not problem_type:
                problem_type = ProblemType.objects.filter(topic=topic).first()
            Formula.objects.get_or_create(
                topic=topic,
                name=name,
                defaults={
                    "formula_latex": expr,
                    "description": description,
                    "problem_type": problem_type,
                    "variables": [],
                    "example_usage": "",
                },
            )

    def _seed_questions(self, topics, user):
        questions_data = [
            {
                "topic_slug": "percentage",
                "question_text": "What is 20% of 250?",
                "correct_answer": "50",
                "difficulty": "easy",
                "explanation_concept": "To find x% of a number, multiply the number by x/100.",
                "explanation_approach": "Convert 20% to a fraction and multiply by 250.",
                "explanation_steps": ["20% = 20/100 = 0.2", "0.2 * 250 = 50"],
                "solution_steps": [
                    {"step_number": 1, "title": "Convert percentage to fraction", "description": "20% = 20/100 = 0.2"},
                    {"step_number": 2, "title": "Multiply by the given number", "description": "0.2 * 250 = 50"},
                ],
                "shortcut": {"title": "Direct multiplication", "description": "20% = 1/5. So 250 / 5 = 50.", "formula": "x% = x/100", "example": "20% of 250 = (20*250)/100 = 50"},
                "tags": ["percentage", "basic"],
            },
            {
                "topic_slug": "percentage",
                "question_text": "A number is increased from 200 to 250. What is the percentage increase?",
                "correct_answer": "25%",
                "difficulty": "easy",
                "explanation_concept": "Percentage increase = ((New - Old) / Old) × 100.",
                "explanation_approach": "Find the difference and divide by the original value.",
                "explanation_steps": ["Increase = 250 - 200 = 50", "Percentage increase = (50 / 200) × 100 = 25%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find the increase", "description": "250 - 200 = 50"},
                    {"step_number": 2, "title": "Compute percentage increase", "description": "(50 / 200) × 100 = 25%"},
                ],
                "shortcut": {"title": "Quick estimate", "description": "50 is one-fourth of 200, so 25%.", "formula": "", "example": ""},
                "tags": ["percentage", "increase"],
            },
            {
                "topic_slug": "profit-loss",
                "question_text": "A shopkeeper buys an article for ₹400 and sells it for ₹500. What is his profit percent?",
                "correct_answer": "25%",
                "difficulty": "easy",
                "explanation_concept": "Profit = SP - CP. Profit % = (Profit / CP) × 100.",
                "explanation_approach": "Calculate profit then divide by cost price.",
                "explanation_steps": ["Profit = 500 - 400 = 100", "Profit % = (100 / 400) × 100 = 25%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Calculate profit", "description": "500 - 400 = 100"},
                    {"step_number": 2, "title": "Calculate profit percentage", "description": "(100 / 400) × 100 = 25%"},
                ],
                "shortcut": {"title": "Direct formula", "description": "Profit % = ((SP - CP) / CP) * 100.", "formula": "", "example": ""},
                "tags": ["profit-loss", "basic"],
            },
            {
                "topic_slug": "profit-loss",
                "question_text": "A sells an article to B at 20% profit. B sells to C at 10% profit. Find overall profit percent.",
                "correct_answer": "32%",
                "difficulty": "medium",
                "explanation_concept": "For successive percentage changes, use multiplicative formula.",
                "explanation_approach": "Apply the successive profit formula: (1 + x/100)(1 + y/100) - 1.",
                "explanation_steps": ["Overall factor = 1.20 * 1.10 = 1.32", "Overall profit % = 32%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Compute combined factor", "description": "1.20 * 1.10 = 1.32"},
                    {"step_number": 2, "title": "Convert to percentage", "description": "1.32 - 1 = 0.32 => 32%"},
                ],
                "shortcut": {"title": "Successive formula", "description": "Successive profit = x + y + xy/100.", "formula": "", "example": "20 + 10 + (20*10)/100 = 32%"},
                "tags": ["profit-loss", "successive"],
            },
            {
                "topic_slug": "average",
                "question_text": "The average of 5 numbers is 20. If one number is excluded, the average becomes 18. What is the excluded number?",
                "correct_answer": "28",
                "difficulty": "medium",
                "explanation_concept": "Sum = Average × Count. Use the change in average to find the removed value.",
                "explanation_approach": "Find total sum, find sum of remaining numbers, subtract.",
                "explanation_steps": ["Sum of 5 numbers = 5 * 20 = 100", "Sum of 4 numbers = 4 * 18 = 72", "Excluded number = 100 - 72 = 28"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find total sum", "description": "5 * 20 = 100"},
                    {"step_number": 2, "title": "Find remaining sum", "description": "4 * 18 = 72"},
                    {"step_number": 3, "title": "Compute excluded number", "description": "100 - 72 = 28"},
                ],
                "shortcut": {"title": "Direct difference", "description": "Excluded = (Change in avg) * (remaining count) + new avg.", "formula": "", "example": "2*4 + 18 = 26 + 2 = 28"},
                "tags": ["average", "basic"],
            },
            {
                "topic_slug": "simple-interest",
                "question_text": "A sum of money doubles itself in 8 years at simple interest. What is the rate of interest?",
                "correct_answer": "12.5%",
                "difficulty": "medium",
                "explanation_concept": "For SI, amount doubles when SI equals principal.",
                "explanation_approach": "Use SI = P * R * T / 100 and set SI = P.",
                "explanation_steps": ["SI = P => P*R*T/100 = P", "R*T/100 = 1 => R*8/100 = 1", "R = 100/8 = 12.5%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Set up equation", "description": "SI = Principal because amount doubles."},
                    {"step_number": 2, "title": "Solve for R", "description": "R = 100 / T = 100 / 8 = 12.5%"},
                ],
                "shortcut": {"title": "Doubling trick", "description": "If sum doubles in T years at SI, rate = 100/T %.", "formula": "", "example": "T=8 => R = 100/8 = 12.5%"},
                "tags": ["simple-interest", "rate"],
            },
            {
                "topic_slug": "compound-interest",
                "question_text": "Find the compound interest on ₹1000 for 2 years at 10% per annum compounded annually.",
                "correct_answer": "₹210",
                "difficulty": "easy",
                "explanation_concept": "CI = P * ((1 + R/100)^T - 1).",
                "explanation_approach": "Plug values into the compound interest formula.",
                "explanation_steps": ["Amount = 1000 * (1 + 10/100)^2 = 1000 * 1.21 = 1210", "CI = 1210 - 1000 = 210"],
                "solution_steps": [
                    {"step_number": 1, "title": "Compute amount", "description": "1000 * (1.1)^2 = 1210"},
                    {"step_number": 2, "title": "Compute CI", "description": "1210 - 1000 = 210"},
                ],
                "shortcut": {"title": "Net effect", "description": "For 2 years, effective rate = 2R + R^2/100. CI = P * (effective rate)/100.", "formula": "", "example": "20 + 1 = 21%. 1000 * 0.21 = 210"},
                "tags": ["compound-interest", "basic"],
            },
            {
                "topic_slug": "time-work",
                "question_text": "A can finish a work in 12 days and B can finish the same work in 15 days. If they work together, how many days will they take to finish the work?",
                "correct_answer": "20/3 days",
                "difficulty": "easy",
                "explanation_concept": "Combined efficiency is the sum of individual efficiencies.",
                "explanation_approach": "Find one-day work for each person, add them, then find total days.",
                "explanation_steps": ["A's one day work = 1/12", "B's one day work = 1/15", "Together = 1/12 + 1/15 = 9/60 = 3/20", "Days = 1 / (3/20) = 20/3"],
                "solution_steps": [
                    {"step_number": 1, "title": "One-day work", "description": "A = 1/12, B = 1/15"},
                    {"step_number": 2, "title": "Add efficiencies", "description": "1/12 + 1/15 = 3/20"},
                    {"step_number": 3, "title": "Compute days", "description": "1 / (3/20) = 20/3"},
                ],
                "shortcut": {"title": "LCM method", "description": "Take LCM of days as total work units. Sum daily units and divide total work by sum.", "formula": "", "example": "LCM = 60. A = 5, B = 4. Sum = 9. Days = 60/9 = 20/3"},
                "tags": ["time-work", "basic"],
            },
            {
                "topic_slug": "time-speed-distance",
                "question_text": "A train 120 m long passes a man running at 5 km/h in the same direction in 10 seconds. What is the speed of the train?",
                "correct_answer": "48.2 km/h",
                "difficulty": "medium",
                "explanation_concept": "Use relative speed when objects move in the same direction.",
                "explanation_approach": "Convert units, find relative speed, then add man's speed.",
                "explanation_steps": ["Relative speed = 120 m / 10 s = 12 m/s = 43.2 km/h", "Train speed = 43.2 + 5 = 48.2 km/h"],
                "solution_steps": [
                    {"step_number": 1, "title": "Convert length/time to speed", "description": "Relative speed = 120/10 = 12 m/s = 43.2 km/h"},
                    {"step_number": 2, "title": "Add man's speed", "description": "Train speed = 43.2 + 5 = 48.2 km/h"},
                ],
                "shortcut": {"title": "Relative speed trick", "description": "Same direction => subtract speeds. Opposite => add.", "formula": "", "example": ""},
                "tags": ["time-speed-distance", "train"],
            },
            {
                "topic_slug": "time-speed-distance",
                "question_text": "A train 100 m long moving at 60 km/h crosses a pole. How long does it take?",
                "correct_answer": "6 seconds",
                "difficulty": "easy",
                "explanation_concept": "Time to cross a pole = train length / speed.",
                "explanation_approach": "Convert speed to m/s and divide length by speed.",
                "explanation_steps": ["60 km/h = 60 * 5/18 = 16.67 m/s", "Time = 100 / 16.67 = 6 seconds"],
                "solution_steps": [
                    {"step_number": 1, "title": "Convert speed", "description": "60 km/h = 50/3 m/s"},
                    {"step_number": 2, "title": "Compute time", "description": "Time = 100 / (50/3) = 6 seconds"},
                ],
                "shortcut": {"title": "Speed conversion", "description": "km/h to m/s multiply by 5/18.", "formula": "", "example": "60 * 5/18 = 50/3 m/s"},
                "tags": ["time-speed-distance", "train", "basic"],
            },
            {
                "topic_slug": "probability",
                "question_text": "A fair coin is tossed two times. What is the probability of getting at least one head?",
                "correct_answer": "3/4",
                "difficulty": "easy",
                "explanation_concept": "Total outcomes for two coin tosses = 4. Favorable = 3.",
                "explanation_approach": "List outcomes and count favorable ones.",
                "explanation_steps": ["Outcomes: HH, HT, TH, TT", "Favorable (at least one H): HH, HT, TH = 3", "Probability = 3/4"],
                "solution_steps": [
                    {"step_number": 1, "title": "List outcomes", "description": "HH, HT, TH, TT"},
                    {"step_number": 2, "title": "Count favorable", "description": "3 outcomes have at least one H"},
                    {"step_number": 3, "title": "Compute probability", "description": "3/4"},
                ],
                "shortcut": {"title": "Complement rule", "description": "P(at least one H) = 1 - P(no H) = 1 - (1/4) = 3/4.", "formula": "", "example": ""},
                "tags": ["probability", "coin"],
            },
            {
                "topic_slug": "permutation-combination",
                "question_text": "How many ways can the letters of the word 'CAT' be arranged?",
                "correct_answer": "6",
                "difficulty": "easy",
                "explanation_concept": "All letters are distinct, so permutations = n!.",
                "explanation_approach": "Use factorial formula for permutations.",
                "explanation_steps": ["n = 3", "Permutations = 3! = 6"],
                "solution_steps": [
                    {"step_number": 1, "title": "Identify distinct letters", "description": "C, A, T are all distinct."},
                    {"step_number": 2, "title": "Apply permutation formula", "description": "3! = 6"},
                ],
                "shortcut": {"title": "Factorial memory", "description": "3! = 6, 4! = 24, 5! = 120.", "formula": "", "example": ""},
                "tags": ["permutation-combination", "arrangement"],
            },
            {
                "topic_slug": "permutation-combination",
                "question_text": "In how many ways can a committee of 3 be chosen from 5 people?",
                "correct_answer": "10",
                "difficulty": "easy",
                "explanation_concept": "Selection is unordered, so use combinations.",
                "explanation_approach": "Apply combination formula C(5, 3).",
                "explanation_steps": ["C(5, 3) = 5! / (3! * 2!) = 10"],
                "solution_steps": [
                    {"step_number": 1, "title": "Apply combination formula", "description": "C(5,3) = 10"},
                ],
                "shortcut": {"title": "Remember C(n,r)", "description": "C(5,3) = C(5,2) = 10.", "formula": "", "example": ""},
                "tags": ["permutation-combination", "selection"],
            },
            {
                "topic_slug": "mixtures-allegations",
                "question_text": "A mixture of alcohol and water contains 20% alcohol. If 5 litres of water is added, the percentage of alcohol becomes 16%. Find the original quantity of the mixture.",
                "correct_answer": "20 litres",
                "difficulty": "medium",
                "explanation_concept": "Keep the quantity of alcohol constant when water is added.",
                "explanation_approach": "Set up equation based on constant alcohol quantity.",
                "explanation_steps": ["Let original mixture = x litres", "Alcohol = 0.2x", "After adding 5L water: alcohol % = 0.2x / (x+5) = 0.16", "0.2x = 0.16x + 0.8 => 0.04x = 0.8 => x = 20"],
                "solution_steps": [
                    {"step_number": 1, "title": "Set variables", "description": "Let original quantity = x litres."},
                    {"step_number": 2, "title": "Write alcohol equation", "description": "0.2x = 0.16(x + 5)"},
                    {"step_number": 3, "title": "Solve for x", "description": "x = 20 litres"},
                ],
                "shortcut": {"title": "Allegation method", "description": "Use allegation to find mixing ratios when needed.", "formula": "", "example": ""},
                "tags": ["mixtures-allegations", "basic"],
            },
            {
                "topic_slug": "data-interpretation",
                "question_text": "A table shows sales of 4 quarters: 200, 300, 250, 350. What is the average quarterly sale?",
                "correct_answer": "275",
                "difficulty": "easy",
                "explanation_concept": "Average = sum of values / count.",
                "explanation_approach": "Add all quarterly sales and divide by 4.",
                "explanation_steps": ["Sum = 200 + 300 + 250 + 350 = 1100", "Average = 1100 / 4 = 275"],
                "solution_steps": [
                    {"step_number": 1, "title": "Sum the values", "description": "200 + 300 + 250 + 350 = 1100"},
                    {"step_number": 2, "title": "Divide by count", "description": "1100 / 4 = 275"},
                ],
                "shortcut": {"title": "Quick addition", "description": "Pair 200+350 = 550 and 300+250 = 550 => 1100.", "formula": "", "example": ""},
                "tags": ["data-interpretation", "average", "table"],
            },
            {
                "topic_slug": "hcf-lcm",
                "question_text": "Find the HCF of 12, 18, and 24.",
                "correct_answer": "6",
                "difficulty": "easy",
                "explanation_concept": "HCF is the largest number that divides all given numbers.",
                "explanation_approach": "Use prime factorization or Euclidean method.",
                "explanation_steps": ["Factors of 12: 1,2,3,4,6,12", "Factors of 18: 1,2,3,6,18", "Factors of 24: 1,2,3,4,6,8,12,24", "Common factors: 1,2,3,6 => HCF = 6"],
                "solution_steps": [
                    {"step_number": 1, "title": "List factors", "description": "List factors of each number."},
                    {"step_number": 2, "title": "Identify common factors", "description": "Common factors: 1, 2, 3, 6"},
                    {"step_number": 3, "title": "Pick the largest", "description": "HCF = 6"},
                ],
                "shortcut": {"title": "Prime factorization", "description": "12=2^2*3, 18=2*3^2, 24=2^3*3. Common: 2*3 = 6.", "formula": "", "example": ""},
                "tags": ["hcf-lcm", "basic"],
            },
            {
                "topic_slug": "number-system",
                "question_text": "What is the remainder when 120 is divided by 7?",
                "correct_answer": "1",
                "difficulty": "easy",
                "explanation_concept": "Remainder is what is left after division.",
                "explanation_approach": "Perform division and note the remainder.",
                "explanation_steps": ["120 / 7 = 17 remainder 1", "Because 7 * 17 = 119 and 120 - 119 = 1"],
                "solution_steps": [
                    {"step_number": 1, "title": "Divide", "description": "120 / 7 = 17 remainder 1"},
                ],
                "shortcut": {"title": "Quick check", "description": "Multiples of 7 near 120 are 119 and 126. Remainder = 120 - 119 = 1.", "formula": "", "example": ""},
                "tags": ["number-system", "remainder"],
            },
            {
                "topic_slug": "ages",
                "question_text": "Father is 3 times older than his son. After 10 years, father will be twice as old as his son. What is the father's current age?",
                "correct_answer": "30",
                "difficulty": "medium",
                "explanation_concept": "Set up equations from age relationships.",
                "explanation_approach": "Let son's age = x, father's age = 3x. Write future equation.",
                "explanation_steps": ["Father = 3x, Son = x", "After 10 years: 3x + 10 = 2(x + 10)", "3x + 10 = 2x + 20 => x = 10", "Father = 3 * 10 = 30"],
                "solution_steps": [
                    {"step_number": 1, "title": "Define variables", "description": "Let son's age = x, father = 3x."},
                    {"step_number": 2, "title": "Write future equation", "description": "3x + 10 = 2(x + 10)"},
                    {"step_number": 3, "title": "Solve", "description": "x = 10 => Father = 30"},
                ],
                "shortcut": {"title": "Tabular method", "description": "Create a table of present and future ages.", "formula": "", "example": ""},
                "tags": ["ages", "equations"],
            },
            {
                "topic_slug": "ratio-proportion",
                "question_text": "If A:B = 2:3 and B:C = 4:5, find A:C.",
                "correct_answer": "8:15",
                "difficulty": "easy",
                "explanation_concept": "To combine ratios, make the common term equal.",
                "explanation_approach": "Scale ratios so B values match, then read A:C.",
                "explanation_steps": ["A:B = 2:3 => multiply by 4 => 8:12", "B:C = 4:5 => multiply by 3 => 12:15", "A:C = 8:15"],
                "solution_steps": [
                    {"step_number": 1, "title": "Scale first ratio", "description": "2:3 => 8:12"},
                    {"step_number": 2, "title": "Scale second ratio", "description": "4:5 => 12:15"},
                    {"step_number": 3, "title": "Combine", "description": "A:C = 8:15"},
                ],
                "shortcut": {"title": "LCM of common terms", "description": "Multiply ratios to make the middle term equal.", "formula": "", "example": ""},
                "tags": ["ratio-proportion", "basic"],
            },
            {
                "topic_slug": "number-system",
                "question_text": "The sum of first 50 natural numbers is?",
                "correct_answer": "1275",
                "difficulty": "easy",
                "explanation_concept": "Sum of first n natural numbers = n(n+1)/2.",
                "explanation_approach": "Apply the formula with n = 50.",
                "explanation_steps": ["Sum = 50 * 51 / 2 = 1275"],
                "solution_steps": [
                    {"step_number": 1, "title": "Apply formula", "description": "50 * 51 / 2 = 1275"},
                ],
                "shortcut": {"title": "Formula recall", "description": "Sum = n(n+1)/2.", "formula": "", "example": ""},
                "tags": ["number-system", "series"],
            },
            {
                "topic_slug": "hcf-lcm",
                "question_text": "The LCM of two numbers is 180 and their HCF is 3. If one number is 45, find the other.",
                "correct_answer": "12",
                "difficulty": "medium",
                "explanation_concept": "Product of two numbers = HCF × LCM.",
                "explanation_approach": "Use product formula to find the unknown number.",
                "explanation_steps": ["Let other number = x", "45 * x = 3 * 180", "x = 540 / 45 = 12"],
                "solution_steps": [
                    {"step_number": 1, "title": "Set product equation", "description": "45 * x = 3 * 180"},
                    {"step_number": 2, "title": "Solve for x", "description": "x = 540 / 45 = 12"},
                ],
                "shortcut": {"title": "Product formula", "description": "a * b = HCF * LCM.", "formula": "", "example": ""},
                "tags": ["hcf-lcm", "product"],
            },
            {
                "topic_slug": "time-work",
                "question_text": "If 5 men can complete a work in 10 days, how many men are needed to complete it in 2 days?",
                "correct_answer": "25",
                "difficulty": "easy",
                "explanation_concept": "Men and days are inversely proportional for constant work.",
                "explanation_approach": "Use M1*D1 = M2*D2.",
                "explanation_steps": ["5 * 10 = M2 * 2", "M2 = 50 / 2 = 25"],
                "solution_steps": [
                    {"step_number": 1, "title": "Apply inverse proportion", "description": "M2 = (5 * 10) / 2 = 25"},
                ],
                "shortcut": {"title": "Men-days inverse", "description": "If days halve, men double.", "formula": "", "example": ""},
                "tags": ["time-work", "inverse"],
            },
            {
                "topic_slug": "pipes-cisterns",
                "question_text": "A pipe can fill a tank in 20 minutes. Another pipe can empty it in 30 minutes. If both are opened together, how long will they take to fill the tank?",
                "correct_answer": "60 minutes",
                "difficulty": "medium",
                "explanation_concept": "Net efficiency = inlet efficiency - outlet efficiency.",
                "explanation_approach": "Find combined rate and invert for time.",
                "explanation_steps": ["Inlet rate = 1/20 per min", "Outlet rate = 1/30 per min", "Net rate = 1/20 - 1/30 = 1/60 per min", "Time = 60 minutes"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find net rate", "description": "1/20 - 1/30 = 1/60"},
                    {"step_number": 2, "title": "Invert for time", "description": "60 minutes"},
                ],
                "shortcut": {"title": "Net rate", "description": "Net rate = (a - b) / (a*b) * LCM.", "formula": "", "example": ""},
                "tags": ["pipes-cisterns", "basic"],
            },
            {
                "topic_slug": "problems-trains",
                "question_text": "Two trains of lengths 120 m and 180 m run in opposite directions at 40 km/h and 50 km/h. How long will they take to cross each other?",
                "correct_answer": "12 seconds",
                "difficulty": "medium",
                "explanation_concept": "When objects move in opposite directions, relative speed is the sum.",
                "explanation_approach": "Find relative speed, total length, then time = length / speed.",
                "explanation_steps": ["Total length = 120 + 180 = 300 m", "Relative speed = 40 + 50 = 90 km/h = 25 m/s", "Time = 300 / 25 = 12 seconds"],
                "solution_steps": [
                    {"step_number": 1, "title": "Sum lengths", "description": "120 + 180 = 300 m"},
                    {"step_number": 2, "title": "Compute relative speed", "description": "90 km/h = 25 m/s"},
                    {"step_number": 3, "title": "Compute crossing time", "description": "300 / 25 = 12 seconds"},
                ],
                "shortcut": {"title": "Opposite direction rule", "description": "Add speeds when moving opposite.", "formula": "", "example": ""},
                "tags": ["problems-trains", "relative-speed"],
            },
            {
                "topic_slug": "ages",
                "question_text": "Present ages of A and B are in the ratio 5:6. After 4 years, their ratio will be 6:7. What is B's present age?",
                "correct_answer": "24",
                "difficulty": "medium",
                "explanation_concept": "Set up age equations from given ratios.",
                "explanation_approach": "Let present ages be 5x and 6x. Write future ratio equation.",
                "explanation_steps": ["A = 5x, B = 6x", "After 4 years: (5x+4)/(6x+4) = 6/7", "Cross multiply: 7(5x+4) = 6(6x+4)", "35x + 28 = 36x + 24 => x = 4", "B = 6x = 24"],
                "solution_steps": [
                    {"step_number": 1, "title": "Define variables", "description": "A = 5x, B = 6x."},
                    {"step_number": 2, "title": "Write ratio equation", "description": "(5x+4)/(6x+4) = 6/7."},
                    {"step_number": 3, "title": "Solve for x", "description": "x = 4."},
                    {"step_number": 4, "title": "Compute B's age", "description": "6 * 4 = 24."},
                ],
                "shortcut": {"title": "Direct cross-multiplication", "description": "Cross-multiply ratios and solve linear equation.", "formula": "", "example": ""},
                "tags": ["ages", "ratio"],
            },
            {
                "topic_slug": "average",
                "question_text": "A batsman has an average of 40 runs over 15 innings. How many runs must he score in the 16th innings to raise his average to 42?",
                "correct_answer": "72",
                "difficulty": "medium",
                "explanation_concept": "Total runs increase by desired average * total innings minus existing total.",
                "explanation_approach": "Find current total, find required total, subtract.",
                "explanation_steps": ["Current total = 40 * 15 = 600", "Required total = 42 * 16 = 672", "Runs needed = 672 - 600 = 72"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find current total", "description": "40 * 15 = 600"},
                    {"step_number": 2, "title": "Find required total", "description": "42 * 16 = 672"},
                    {"step_number": 3, "title": "Compute needed runs", "description": "672 - 600 = 72"},
                ],
                "shortcut": {"title": "Direct formula", "description": "Required score = New avg * n - Old avg * (n-1).", "formula": "", "example": "42*16 - 40*15 = 72"},
                "tags": ["average", "cricket"],
            },
            {
                "topic_slug": "compound-interest",
                "question_text": "What is the effective annual rate if nominal rate is 12% compounded half-yearly?",
                "correct_answer": "12.36%",
                "difficulty": "medium",
                "explanation_concept": "Effective rate accounts for compounding frequency.",
                "explanation_approach": "Use EIR = (1 + R/n)^n - 1.",
                "explanation_steps": ["EIR = (1 + 0.12/2)^2 - 1", "EIR = (1.06)^2 - 1 = 1.1236 - 1 = 0.1236", "Effective rate = 12.36%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Apply EIR formula", "description": "(1 + 0.06)^2 - 1 = 0.1236"},
                    {"step_number": 2, "title": "Convert to percentage", "description": "12.36%"},
                ],
                "shortcut": {"title": "Remember rule of 72", "description": "72 / rate = doubling years approximation.", "formula": "", "example": ""},
                "tags": ["compound-interest", "effective-rate"],
            },
            {
                "topic_slug": "probability",
                "question_text": "A bag contains 4 red and 6 blue balls. Two balls are drawn at random. What is the probability that both are red?",
                "correct_answer": "2/15",
                "difficulty": "medium",
                "explanation_concept": "Probability of both red = C(4,2) / C(10,2).",
                "explanation_approach": "Use combinations since order does not matter.",
                "explanation_steps": ["Total ways to choose 2 from 10 = C(10,2) = 45", "Ways to choose 2 red from 4 = C(4,2) = 6", "Probability = 6/45 = 2/15"],
                "solution_steps": [
                    {"step_number": 1, "title": "Count total combinations", "description": "C(10,2) = 45"},
                    {"step_number": 2, "title": "Count favorable combinations", "description": "C(4,2) = 6"},
                    {"step_number": 3, "title": "Compute probability", "description": "6/45 = 2/15"},
                ],
                "shortcut": {"title": "Combination shortcut", "description": "C(n,2) = n(n-1)/2.", "formula": "", "example": "C(4,2) = 12/2 = 6"},
                "tags": ["probability", "combinations"],
            },
            {
                "topic_slug": "data-interpretation",
                "question_text": "A pie chart shows expenses: Rent 30%, Food 40%, Others 30%. If total income is ₹50000, what is spent on food?",
                "correct_answer": "₹20000",
                "difficulty": "easy",
                "explanation_concept": "Use percentage of total from pie chart.",
                "explanation_approach": "Calculate 40% of 50000.",
                "explanation_steps": ["Food expense = 40% of 50000", "= 0.4 * 50000 = 20000"],
                "solution_steps": [
                    {"step_number": 1, "title": "Compute share", "description": "40% of 50000 = 20000"},
                ],
                "shortcut": {"title": "10% trick", "description": "10% of 50000 = 5000. So 40% = 20000.", "formula": "", "example": ""},
                "tags": ["data-interpretation", "pie-chart", "percentage"],
            },
            {
                "topic_slug": "ratio-proportion",
                "question_text": "Divide ₹6300 among A, B, and C in the ratio 2:3:4. What is B's share?",
                "correct_answer": "₹2100",
                "difficulty": "easy",
                "explanation_concept": "Share = (Part / Sum of parts) * Total.",
                "explanation_approach": "Find sum of ratio parts, then B's share.",
                "explanation_steps": ["Sum of parts = 2 + 3 + 4 = 9", "B's share = (3/9) * 6300 = 2100"],
                "solution_steps": [
                    {"step_number": 1, "title": "Sum ratio parts", "description": "2 + 3 + 4 = 9"},
                    {"step_number": 2, "title": "Compute B's share", "description": "(3/9) * 6300 = 2100"},
                ],
                "shortcut": {"title": "Direct fraction", "description": "B gets 3/9 of total.", "formula": "", "example": ""},
                "tags": ["ratio-proportion", "division"],
            },
            {
                "topic_slug": "number-system",
                "question_text": "Find the unit digit of 7^53.",
                "correct_answer": "7",
                "difficulty": "medium",
                "explanation_concept": "Unit digits of powers repeat in cycles of 4.",
                "explanation_approach": "Find 53 mod 4 and use the corresponding unit digit.",
                "explanation_steps": ["Cycle of 7: 7, 9, 3, 1", "53 mod 4 = 1", "Unit digit = 7"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find cycle position", "description": "53 mod 4 = 1"},
                    {"step_number": 2, "title": "Read unit digit", "description": "7^53 ends with 7"},
                ],
                "shortcut": {"title": "Cyclicity rule", "description": "For 7, cycle = 7,9,3,1. Power mod 4 gives position.", "formula": "", "example": ""},
                "tags": ["number-system", "unit-digit"],
            },
            {
                "topic_slug": "simple-interest",
                "question_text": "At what rate of simple interest will ₹2000 amount to ₹2400 in 4 years?",
                "correct_answer": "5%",
                "difficulty": "easy",
                "explanation_concept": "SI = Amount - Principal.",
                "explanation_approach": "Find SI, then use R = (SI * 100) / (P * T).",
                "explanation_steps": ["SI = 2400 - 2000 = 400", "R = (400 * 100) / (2000 * 4) = 5%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Find SI", "description": "2400 - 2000 = 400"},
                    {"step_number": 2, "title": "Compute rate", "description": "(400 * 100) / (2000 * 4) = 5%"},
                ],
                "shortcut": {"title": "Direct rate formula", "description": "R = (SI * 100) / (P * T).", "formula": "", "example": ""},
                "tags": ["simple-interest", "rate"],
            },
            {
                "topic_slug": "time-speed-distance",
                "question_text": "A person travels from A to B at 40 km/h and returns at 60 km/h. Find his average speed for the whole journey.",
                "correct_answer": "48 km/h",
                "difficulty": "medium",
                "explanation_concept": "For equal distances, average speed = harmonic mean of speeds.",
                "explanation_approach": "Use formula 2ab / (a+b).",
                "explanation_steps": ["Average speed = (2 * 40 * 60) / (40 + 60) = 4800 / 100 = 48 km/h"],
                "solution_steps": [
                    {"step_number": 1, "title": "Apply harmonic mean", "description": "2*40*60 / (40+60) = 48 km/h"},
                ],
                "shortcut": {"title": "Equal distance formula", "description": "2ab/(a+b) for equal distances.", "formula": "", "example": "2*40*60/100 = 48"},
                "tags": ["time-speed-distance", "average-speed"],
            },
            {
                "topic_slug": "profit-loss",
                "question_text": "A man buys an article for ₹300 and sells it for ₹270. What is his loss percent?",
                "correct_answer": "10%",
                "difficulty": "easy",
                "explanation_concept": "Loss = CP - SP. Loss % = (Loss / CP) × 100.",
                "explanation_approach": "Calculate loss and divide by cost price.",
                "explanation_steps": ["Loss = 300 - 270 = 30", "Loss % = (30 / 300) × 100 = 10%"],
                "solution_steps": [
                    {"step_number": 1, "title": "Calculate loss", "description": "300 - 270 = 30"},
                    {"step_number": 2, "title": "Compute loss percentage", "description": "(30 / 300) * 100 = 10%"},
                ],
                "shortcut": {"title": "Direct formula", "description": "Loss % = ((CP - SP) / CP) * 100.", "formula": "", "example": ""},
                "tags": ["profit-loss", "loss"],
            },
            {
                "topic_slug": "percentage",
                "question_text": "If 40% of a number is 160, what is the number?",
                "correct_answer": "400",
                "difficulty": "easy",
                "explanation_concept": "If x% of a number is known, divide by x/100.",
                "explanation_approach": "Number = Given value / (x/100).",
                "explanation_steps": ["Number = 160 / 0.4 = 400"],
                "solution_steps": [
                    {"step_number": 1, "title": "Divide by percentage", "description": "160 / 0.4 = 400"},
                ],
                "shortcut": {"title": "Unitary method", "description": "If 40% = 160, 100% = 160 * (100/40) = 400.", "formula": "", "example": ""},
                "tags": ["percentage", "reverse"],
            },
            {
                "topic_slug": "average",
                "question_text": "A student scored 60, 70, 80, and 90 in four subjects. Find his average.",
                "correct_answer": "75",
                "difficulty": "easy",
                "explanation_concept": "Average = sum of scores / number of subjects.",
                "explanation_approach": "Add all scores and divide by 4.",
                "explanation_steps": ["Sum = 60 + 70 + 80 + 90 = 300", "Average = 300 / 4 = 75"],
                "solution_steps": [
                    {"step_number": 1, "title": "Sum scores", "description": "300"},
                    {"step_number": 2, "title": "Divide by count", "description": "300 / 4 = 75"},
                ],
                "shortcut": {"title": "Quick add", "description": "60+90=150, 70+80=150 => 300.", "formula": "", "example": ""},
                "tags": ["average", "student"],
            },
        ]

        for q in questions_data:
            topic = topics.get(q["topic_slug"])
            if not topic:
                continue
            problem_type = ProblemType.objects.filter(topic=topic).first()
            subtopic = Subtopic.objects.filter(topic=topic).first()
            question, created = Question.objects.get_or_create(
                topic=topic,
                question_text=q["question_text"],
                defaults={
                    "problem_type": problem_type,
                    "subtopic": subtopic,
                    "difficulty": q["difficulty"],
                    "correct_answer": q["correct_answer"],
                    "explanation_concept": q["explanation_concept"],
                    "explanation_approach": q["explanation_approach"],
                    "explanation_steps": q["explanation_steps"],
                    "hints": [],
                    "tags": q["tags"],
                    "is_active": True,
                    "created_by": user,
                },
            )
            if not created:
                continue
            for step_data in q.get("solution_steps", []):
                SolutionStep.objects.get_or_create(
                    question=question,
                    step_number=step_data["step_number"],
                    defaults={
                        "title": step_data["title"],
                        "description": step_data["description"],
                        "latex": "",
                    },
                )
            shortcut_data = q.get("shortcut")
            if shortcut_data:
                Shortcut.objects.get_or_create(
                    question=question,
                    title=shortcut_data["title"],
                    defaults={
                        "description": shortcut_data["description"],
                        "formula": shortcut_data.get("formula", ""),
                        "example": shortcut_data.get("example", ""),
                    },
                )
