from tests.psychology.depression import DepressionTest
from tests.psychology.anxiety import AnxietyTest
from tests.psychology.stress import StressTest
from tests.personality.bigfive import BigFiveTest
from tests.personality.mbti import MBTIPersonalityTest
from tests.esoteric.soul_type import SoulTypeTest
from tests.esoteric.elemental_energy import ElementalEnergyTest
from tests.esoteric.ayurvedic_dosha import AyurvedicDoshaTest
from tests.esoteric.magical_path import MagicalPathTest


class TestFactory:
    TESTS = {
        "depression": DepressionTest,
        "anxiety": AnxietyTest,
        "stress": StressTest,
        "bigfive": BigFiveTest,
        "mbti": MBTIPersonalityTest,
        "soul_type": SoulTypeTest,
        "elemental": ElementalEnergyTest,
        "ayurvedic": AyurvedicDoshaTest,
        "magic_path": MagicalPathTest
    }
    
    @classmethod
    def get_test(cls, test_id):
        return cls.TESTS.get(test_id)
    
    @classmethod
    def get_tests_by_category(cls, category_id):
        return {
            test_id: test_class
            for test_id, test_class in cls.TESTS.items()
            if getattr(test_class, 'category', None) == category_id
        }