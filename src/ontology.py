"""
过敏知识本体（Allergy Ontology）
定义过敏相关的固定概念节点和分类体系
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConceptCategory(str, Enum):
    """概念分类"""
    IMMUNOGLOBULIN = "免疫球蛋白"      # IgE, IgG, IgG4 等
    ALLERGEN = "过敏原"                 # 尘螨、花粉、食物等
    DISEASE = "过敏性疾病"              # 过敏性鼻炎、食物过敏等
    SYMPTOM = "症状"                    # 打喷嚏、皮疹等
    TREATMENT = "治疗方法"              # 免疫治疗、药物治疗等
    DIAGNOSTIC = "诊断方法"             # 皮肤点刺、血清检测等
    CELL = "细胞"                       # 肥大细胞、嗜酸性粒细胞等
    MEDIATOR = "介质"                   # 组胺、白三烯等


@dataclass
class OntologyNode:
    """本体节点"""
    id: str                             # 唯一标识
    name_zh: str                        # 中文名称
    name_en: Optional[str]              # 英文名称
    category: ConceptCategory           # 分类
    aliases: list[str]                  # 别名列表
    parent_id: Optional[str] = None     # 父节点ID
    description: Optional[str] = None   # 描述


# 预定义的过敏知识本体
ALLERGY_ONTOLOGY: dict[str, OntologyNode] = {
    # ===== 免疫球蛋白 =====
    "ige": OntologyNode(
        id="ige",
        name_zh="免疫球蛋白E",
        name_en="Immunoglobulin E",
        category=ConceptCategory.IMMUNOGLOBULIN,
        aliases=["IgE", "免疫球蛋白E", "Immunoglobulin E"],
        description="介导I型超敏反应的主要抗体，与过敏反应密切相关"
    ),
    "igg": OntologyNode(
        id="igg",
        name_zh="免疫球蛋白G",
        name_en="Immunoglobulin G",
        category=ConceptCategory.IMMUNOGLOBULIN,
        aliases=["IgG", "免疫球蛋白G", "Immunoglobulin G"],
        description="血清中含量最高的免疫球蛋白"
    ),
    "igg4": OntologyNode(
        id="igg4",
        name_zh="免疫球蛋白G4",
        name_en="Immunoglobulin G4",
        category=ConceptCategory.IMMUNOGLOBULIN,
        aliases=["IgG4", "免疫球蛋白G4"],
        parent_id="igg",
        description="IgG的亚型，在免疫耐受中发挥作用"
    ),
    "sige": OntologyNode(
        id="sige",
        name_zh="特异性IgE",
        name_en="Specific IgE",
        category=ConceptCategory.IMMUNOGLOBULIN,
        aliases=["sIgE", "特异性IgE", "specific IgE"],
        parent_id="ige",
        description="针对特定过敏原的IgE抗体"
    ),
    
    # ===== 过敏原 - 吸入性 =====
    "dust_mite": OntologyNode(
        id="dust_mite",
        name_zh="尘螨",
        name_en="Dust Mite",
        category=ConceptCategory.ALLERGEN,
        aliases=["尘螨", "屋尘螨", "粉尘螨", "户尘螨", "dust mite", "Der p", "Der f"],
        description="最常见的室内吸入性过敏原"
    ),
    "pollen": OntologyNode(
        id="pollen",
        name_zh="花粉",
        name_en="Pollen",
        category=ConceptCategory.ALLERGEN,
        aliases=["花粉", "pollen", "树花粉", "草花粉"],
        description="季节性过敏的主要诱因"
    ),
    "mold": OntologyNode(
        id="mold",
        name_zh="霉菌",
        name_en="Mold",
        category=ConceptCategory.ALLERGEN,
        aliases=["霉菌", "真菌", "mold", "fungus", "曲霉", "链格孢"],
        description="常见的室内外过敏原"
    ),
    "animal_dander": OntologyNode(
        id="animal_dander",
        name_zh="动物皮屑",
        name_en="Animal Dander",
        category=ConceptCategory.ALLERGEN,
        aliases=["动物皮屑", "猫毛", "狗毛", "宠物过敏", "cat dander", "dog dander"],
        description="宠物相关的过敏原"
    ),
    
    # ===== 过敏原 - 食物 =====
    "milk": OntologyNode(
        id="milk",
        name_zh="牛奶",
        name_en="Milk",
        category=ConceptCategory.ALLERGEN,
        aliases=["牛奶", "乳制品", "milk", "dairy", "牛奶蛋白"],
        description="儿童常见食物过敏原"
    ),
    "egg": OntologyNode(
        id="egg",
        name_zh="鸡蛋",
        name_en="Egg",
        category=ConceptCategory.ALLERGEN,
        aliases=["鸡蛋", "蛋", "egg", "卵清蛋白", "卵黄"],
        description="常见食物过敏原"
    ),
    "peanut": OntologyNode(
        id="peanut",
        name_zh="花生",
        name_en="Peanut",
        category=ConceptCategory.ALLERGEN,
        aliases=["花生", "peanut", "Ara h"],
        description="可引起严重过敏反应的食物"
    ),
    "wheat": OntologyNode(
        id="wheat",
        name_zh="小麦",
        name_en="Wheat",
        category=ConceptCategory.ALLERGEN,
        aliases=["小麦", "麸质", "wheat", "gluten", "面筋"],
        description="常见食物过敏原"
    ),
    "seafood": OntologyNode(
        id="seafood",
        name_zh="海鲜",
        name_en="Seafood",
        category=ConceptCategory.ALLERGEN,
        aliases=["海鲜", "虾", "蟹", "贝类", "鱼", "shrimp", "crab", "shellfish"],
        description="常见食物过敏原"
    ),
    
    # ===== 过敏性疾病 =====
    "allergic_rhinitis": OntologyNode(
        id="allergic_rhinitis",
        name_zh="过敏性鼻炎",
        name_en="Allergic Rhinitis",
        category=ConceptCategory.DISEASE,
        aliases=["过敏性鼻炎", "变应性鼻炎", "AR", "allergic rhinitis", "hay fever", "花粉症"],
        description="由过敏原引起的鼻黏膜炎症"
    ),
    "food_allergy": OntologyNode(
        id="food_allergy",
        name_zh="食物过敏",
        name_en="Food Allergy",
        category=ConceptCategory.DISEASE,
        aliases=["食物过敏", "food allergy", "食物变态反应"],
        description="对特定食物的免疫反应"
    ),
    "atopic_dermatitis": OntologyNode(
        id="atopic_dermatitis",
        name_zh="特应性皮炎",
        name_en="Atopic Dermatitis",
        category=ConceptCategory.DISEASE,
        aliases=["特应性皮炎", "AD", "湿疹", "atopic dermatitis", "eczema"],
        description="慢性炎症性皮肤病"
    ),
    "asthma": OntologyNode(
        id="asthma",
        name_zh="哮喘",
        name_en="Asthma",
        category=ConceptCategory.DISEASE,
        aliases=["哮喘", "支气管哮喘", "asthma", "过敏性哮喘"],
        description="气道慢性炎症性疾病"
    ),
    "urticaria": OntologyNode(
        id="urticaria",
        name_zh="荨麻疹",
        name_en="Urticaria",
        category=ConceptCategory.DISEASE,
        aliases=["荨麻疹", "urticaria", "hives", "风疹块"],
        description="皮肤黏膜血管通透性增加引起的局限性水肿"
    ),
    "anaphylaxis": OntologyNode(
        id="anaphylaxis",
        name_zh="过敏性休克",
        name_en="Anaphylaxis",
        category=ConceptCategory.DISEASE,
        aliases=["过敏性休克", "anaphylaxis", "严重过敏反应", "过敏反应"],
        description="严重的全身性过敏反应"
    ),
    
    # ===== 诊断方法 =====
    "skin_prick_test": OntologyNode(
        id="skin_prick_test",
        name_zh="皮肤点刺试验",
        name_en="Skin Prick Test",
        category=ConceptCategory.DIAGNOSTIC,
        aliases=["皮肤点刺试验", "SPT", "skin prick test", "点刺试验"],
        description="常用的过敏原检测方法"
    ),
    "serum_sige": OntologyNode(
        id="serum_sige",
        name_zh="血清特异性IgE检测",
        name_en="Serum Specific IgE Test",
        category=ConceptCategory.DIAGNOSTIC,
        aliases=["血清特异性IgE检测", "sIgE检测", "体外检测", "ImmunoCAP"],
        description="体外过敏原检测方法"
    ),
    "component_resolved_diagnosis": OntologyNode(
        id="component_resolved_diagnosis",
        name_zh="组分解析诊断",
        name_en="Component Resolved Diagnosis",
        category=ConceptCategory.DIAGNOSTIC,
        aliases=["组分解析诊断", "CRD", "分子诊断", "component resolved diagnosis"],
        description="基于过敏原组分的精准诊断"
    ),
    
    # ===== 治疗方法 =====
    "immunotherapy": OntologyNode(
        id="immunotherapy",
        name_zh="免疫治疗",
        name_en="Allergen Immunotherapy",
        category=ConceptCategory.TREATMENT,
        aliases=["免疫治疗", "AIT", "脱敏治疗", "allergen immunotherapy", "特异性免疫治疗"],
        description="通过逐渐增加过敏原暴露来诱导耐受"
    ),
    "antihistamine": OntologyNode(
        id="antihistamine",
        name_zh="抗组胺药",
        name_en="Antihistamine",
        category=ConceptCategory.TREATMENT,
        aliases=["抗组胺药", "antihistamine", "抗过敏药", "H1受体拮抗剂"],
        description="阻断组胺作用的药物"
    ),
    
    # ===== 细胞 =====
    "mast_cell": OntologyNode(
        id="mast_cell",
        name_zh="肥大细胞",
        name_en="Mast Cell",
        category=ConceptCategory.CELL,
        aliases=["肥大细胞", "mast cell"],
        description="释放组胺等介质的效应细胞"
    ),
    "eosinophil": OntologyNode(
        id="eosinophil",
        name_zh="嗜酸性粒细胞",
        name_en="Eosinophil",
        category=ConceptCategory.CELL,
        aliases=["嗜酸性粒细胞", "eosinophil", "EOS"],
        description="参与过敏性炎症的白细胞"
    ),
    
    # ===== 介质 =====
    "histamine": OntologyNode(
        id="histamine",
        name_zh="组胺",
        name_en="Histamine",
        category=ConceptCategory.MEDIATOR,
        aliases=["组胺", "histamine"],
        description="主要的过敏介质"
    ),
}


def get_all_aliases() -> dict[str, str]:
    """获取所有别名到节点ID的映射"""
    alias_map = {}
    for node_id, node in ALLERGY_ONTOLOGY.items():
        for alias in node.aliases:
            alias_map[alias.lower()] = node_id
    return alias_map


def find_nodes_in_text(text: str) -> list[OntologyNode]:
    """
    在文本中查找匹配的本体节点
    
    Args:
        text: 要搜索的文本
        
    Returns:
        匹配的节点列表
    """
    found_nodes = []
    text_lower = text.lower()
    alias_map = get_all_aliases()
    
    matched_ids = set()
    for alias, node_id in alias_map.items():
        if alias in text_lower and node_id not in matched_ids:
            matched_ids.add(node_id)
            found_nodes.append(ALLERGY_ONTOLOGY[node_id])
    
    return found_nodes


def get_nodes_by_category(category: ConceptCategory) -> list[OntologyNode]:
    """按类别获取节点"""
    return [
        node for node in ALLERGY_ONTOLOGY.values() 
        if node.category == category
    ]


def get_node_by_id(node_id: str) -> Optional[OntologyNode]:
    """根据ID获取节点"""
    return ALLERGY_ONTOLOGY.get(node_id)
