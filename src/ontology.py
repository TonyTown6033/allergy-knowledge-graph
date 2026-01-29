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
    NUTRIENT = "营养素"                 # 维生素、矿物质、脂肪酸等
    PROBIOTIC = "益生菌"                # 益生菌及其菌株


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

    # ===== 营养素 =====
    "nutrient": OntologyNode(
        id="nutrient",
        name_zh="营养素",
        name_en="Nutrient",
        category=ConceptCategory.NUTRIENT,
        aliases=["营养素", "nutrient", "营养成分"],
        description="维持人体正常生理功能所需的基本成分"
    ),
    "vitamin_d": OntologyNode(
        id="vitamin_d",
        name_zh="维生素D",
        name_en="Vitamin D",
        category=ConceptCategory.NUTRIENT,
        aliases=["维生素D", "vitamin D", "D3", "胆钙化醇"],
        parent_id="nutrient",
        description="脂溶性维生素，参与免疫调节与钙磷代谢"
    ),
    "vitamin_a": OntologyNode(
        id="vitamin_a",
        name_zh="维生素A",
        name_en="Vitamin A",
        category=ConceptCategory.NUTRIENT,
        aliases=["维生素A", "vitamin A", "视黄醇"],
        parent_id="nutrient",
        description="脂溶性维生素，维持上皮屏障与免疫功能"
    ),
    "vitamin_c": OntologyNode(
        id="vitamin_c",
        name_zh="维生素C",
        name_en="Vitamin C",
        category=ConceptCategory.NUTRIENT,
        aliases=["维生素C", "vitamin C", "抗坏血酸"],
        parent_id="nutrient",
        description="水溶性维生素，参与抗氧化与免疫反应"
    ),
    "omega_3": OntologyNode(
        id="omega_3",
        name_zh="Omega-3脂肪酸",
        name_en="Omega-3 Fatty Acids",
        category=ConceptCategory.NUTRIENT,
        aliases=["Omega-3", "ω-3", "DHA", "EPA", "ALA", "omega-3"],
        parent_id="nutrient",
        description="多不饱和脂肪酸，具有抗炎作用"
    ),
    "zinc": OntologyNode(
        id="zinc",
        name_zh="锌",
        name_en="Zinc",
        category=ConceptCategory.NUTRIENT,
        aliases=["锌", "zinc", "Zn"],
        parent_id="nutrient",
        description="必需微量元素，参与免疫细胞功能"
    ),
    "selenium": OntologyNode(
        id="selenium",
        name_zh="硒",
        name_en="Selenium",
        category=ConceptCategory.NUTRIENT,
        aliases=["硒", "selenium", "Se"],
        parent_id="nutrient",
        description="必需微量元素，参与抗氧化与免疫调节"
    ),
    "dietary_fiber": OntologyNode(
        id="dietary_fiber",
        name_zh="膳食纤维",
        name_en="Dietary Fiber",
        category=ConceptCategory.NUTRIENT,
        aliases=["膳食纤维", "dietary fiber", "fiber", "纤维"],
        parent_id="nutrient",
        description="不可消化的碳水化合物，支持肠道菌群"
    ),

    # ===== 益生菌 =====
    "probiotic": OntologyNode(
        id="probiotic",
        name_zh="益生菌",
        name_en="Probiotics",
        category=ConceptCategory.PROBIOTIC,
        aliases=["益生菌", "probiotics", "probiotic"],
        description="适量摄入对宿主有益的活微生物"
    ),
    "lactobacillus_rhamnosus": OntologyNode(
        id="lactobacillus_rhamnosus",
        name_zh="鼠李糖乳酪杆菌",
        name_en="Lactobacillus rhamnosus",
        category=ConceptCategory.PROBIOTIC,
        aliases=["鼠李糖乳酪杆菌", "Lactobacillus rhamnosus", "L. rhamnosus"],
        parent_id="lactobacillus",
        description="常见益生菌种，包含多种研究菌株"
    ),
    "lactobacillus_paracasei": OntologyNode(
        id="lactobacillus_paracasei",
        name_zh="副干酪乳杆菌",
        name_en="Lactobacillus paracasei",
        category=ConceptCategory.PROBIOTIC,
        aliases=["副干酪乳杆菌", "Lactobacillus paracasei", "L. paracasei"],
        parent_id="lactobacillus",
        description="常见益生菌种，具有免疫调节作用"
    ),
    "lactobacillus_reuteri": OntologyNode(
        id="lactobacillus_reuteri",
        name_zh="罗伊氏乳杆菌",
        name_en="Lactobacillus reuteri",
        category=ConceptCategory.PROBIOTIC,
        aliases=["罗伊氏乳杆菌", "Lactobacillus reuteri", "L. reuteri"],
        parent_id="lactobacillus",
        description="报道可缓解过敏相关症状并调节肠道菌群与免疫反应"
    ),
    "bifidobacterium_animalis_lactis": OntologyNode(
        id="bifidobacterium_animalis_lactis",
        name_zh="动物双歧杆菌乳亚种",
        name_en="Bifidobacterium animalis subsp. lactis",
        category=ConceptCategory.PROBIOTIC,
        aliases=[
            "动物双歧杆菌乳亚种",
            "Bifidobacterium animalis subsp. lactis",
            "B. animalis subsp. lactis",
        ],
        parent_id="bifidobacterium",
        description="常见益生菌亚种，常用于功能食品"
    ),
    "bifidobacterium_breve": OntologyNode(
        id="bifidobacterium_breve",
        name_zh="短双歧杆菌",
        name_en="Bifidobacterium breve",
        category=ConceptCategory.PROBIOTIC,
        aliases=["短双歧杆菌", "Bifidobacterium breve", "B. breve"],
        parent_id="bifidobacterium",
        description="婴幼儿肠道常见双歧杆菌种"
    ),
    "bifidobacterium_longum": OntologyNode(
        id="bifidobacterium_longum",
        name_zh="长双歧杆菌",
        name_en="Bifidobacterium longum",
        category=ConceptCategory.PROBIOTIC,
        aliases=["长双歧杆菌", "Bifidobacterium longum", "B. longum"],
        parent_id="bifidobacterium",
        description="常见双歧杆菌种，部分菌株用于过敏相关研究"
    ),
    "bifidobacterium_infantis": OntologyNode(
        id="bifidobacterium_infantis",
        name_zh="婴儿双歧杆菌",
        name_en="Bifidobacterium longum subsp. infantis",
        category=ConceptCategory.PROBIOTIC,
        aliases=[
            "婴儿双歧杆菌",
            "Bifidobacterium infantis",
            "Bifidobacterium longum subsp. infantis",
            "B. infantis",
        ],
        parent_id="bifidobacterium_longum",
        description="婴幼儿肠道优势菌群，擅长利用母乳低聚糖"
    ),
    "lactobacillus": OntologyNode(
        id="lactobacillus",
        name_zh="乳酸杆菌",
        name_en="Lactobacillus",
        category=ConceptCategory.PROBIOTIC,
        aliases=["乳酸杆菌", "lactobacillus", "Lactobacillus"],
        parent_id="probiotic",
        description="常见益生菌属，参与维持肠道生态"
    ),
    "bifidobacterium": OntologyNode(
        id="bifidobacterium",
        name_zh="双歧杆菌",
        name_en="Bifidobacterium",
        category=ConceptCategory.PROBIOTIC,
        aliases=["双歧杆菌", "bifidobacterium", "Bifidobacterium"],
        parent_id="probiotic",
        description="常见益生菌属，改善肠道屏障功能"
    ),
    "saccharomyces_boulardii": OntologyNode(
        id="saccharomyces_boulardii",
        name_zh="布拉氏酵母菌",
        name_en="Saccharomyces boulardii",
        category=ConceptCategory.PROBIOTIC,
        aliases=["布拉氏酵母菌", "Saccharomyces boulardii", "S. boulardii"],
        parent_id="probiotic",
        description="常见益生菌酵母，耐酸耐胆汁"
    ),
    "l_rhamnosus_lgg": OntologyNode(
        id="l_rhamnosus_lgg",
        name_zh="鼠李糖乳酪杆菌GG",
        name_en="Lactobacillus rhamnosus GG",
        category=ConceptCategory.PROBIOTIC,
        aliases=["LGG", "鼠李糖乳酪杆菌GG", "Lactobacillus rhamnosus GG"],
        parent_id="lactobacillus_rhamnosus",
        description="经典益生菌菌株，常用于过敏相关研究"
    ),
    "l_rhamnosus_hn001": OntologyNode(
        id="l_rhamnosus_hn001",
        name_zh="鼠李糖乳酪杆菌HN001",
        name_en="Lactobacillus rhamnosus HN001",
        category=ConceptCategory.PROBIOTIC,
        aliases=["HN001", "鼠李糖乳酪杆菌HN001", "Lactobacillus rhamnosus HN001"],
        parent_id="lactobacillus_rhamnosus",
        description="报道用于孕产妇及婴幼儿过敏相关研究的菌株"
    ),
    "l_rhamnosus_hn019": OntologyNode(
        id="l_rhamnosus_hn019",
        name_zh="鼠李糖乳酪杆菌HN019",
        name_en="Lactobacillus rhamnosus HN019",
        category=ConceptCategory.PROBIOTIC,
        aliases=["HN019", "鼠李糖乳酪杆菌HN019", "Lactobacillus rhamnosus HN019"],
        parent_id="lactobacillus_rhamnosus",
        description="过敏相关研究中常对比使用的菌株"
    ),
    "l_paracasei_lc_zhang": OntologyNode(
        id="l_paracasei_lc_zhang",
        name_zh="副干酪乳杆菌Zhang",
        name_en="Lactobacillus paracasei LC-Zhang",
        category=ConceptCategory.PROBIOTIC,
        aliases=["LC-Zhang", "副干酪乳杆菌Zhang", "Lactobacillus paracasei LC-Zhang"],
        parent_id="lactobacillus_paracasei",
        description="报道可降低IgE水平并改善过敏症状的菌株"
    ),
    "b_animalis_lactis_probio_m8": OntologyNode(
        id="b_animalis_lactis_probio_m8",
        name_zh="动物双歧杆菌乳亚种Probio-M8",
        name_en="Bifidobacterium animalis subsp. lactis Probio-M8",
        category=ConceptCategory.PROBIOTIC,
        aliases=[
            "Probio-M8",
            "动物双歧杆菌乳亚种Probio-M8",
            "Bifidobacterium animalis subsp. lactis Probio-M8",
        ],
        parent_id="bifidobacterium_animalis_lactis",
        description="报道可调节免疫并缓解食物过敏反应的菌株"
    ),
    "l_paracasei_probio_37": OntologyNode(
        id="l_paracasei_probio_37",
        name_zh="副干酪乳杆菌Probio-37",
        name_en="Lactobacillus paracasei Probio-37",
        category=ConceptCategory.PROBIOTIC,
        aliases=["Probio-37", "副干酪乳杆菌Probio-37", "Lactobacillus paracasei Probio-37"],
        parent_id="lactobacillus_paracasei",
        description="报道可改善过敏性鼻炎症状的菌株"
    ),
    "l_rhamnosus_r7041": OntologyNode(
        id="l_rhamnosus_r7041",
        name_zh="鼠李糖乳酪杆菌R7041",
        name_en="Lactobacillus rhamnosus R7041",
        category=ConceptCategory.PROBIOTIC,
        aliases=["R7041", "鼠李糖乳酪杆菌R7041", "Lactobacillus rhamnosus R7041"],
        parent_id="lactobacillus_rhamnosus",
        description="报道可降低皮肤过敏症状并调节相关细胞因子的菌株"
    ),
    "l_rhamnosus_mp108": OntologyNode(
        id="l_rhamnosus_mp108",
        name_zh="鼠李糖乳酪杆菌MP108",
        name_en="Lactobacillus rhamnosus MP108",
        category=ConceptCategory.PROBIOTIC,
        aliases=["MP108", "鼠李糖乳酪杆菌MP108", "Lactobacillus rhamnosus MP108"],
        parent_id="lactobacillus_rhamnosus",
        description="报道可改善儿童特应性皮炎与过敏症状的菌株"
    ),
    "b_breve_m16v": OntologyNode(
        id="b_breve_m16v",
        name_zh="短双歧杆菌M-16V",
        name_en="Bifidobacterium breve M-16V",
        category=ConceptCategory.PROBIOTIC,
        aliases=["M-16V", "短双歧杆菌M-16V", "Bifidobacterium breve M-16V"],
        parent_id="bifidobacterium_breve",
        description="报道可降低婴幼儿过敏风险的菌株"
    ),
    "b_longum_bb536": OntologyNode(
        id="b_longum_bb536",
        name_zh="长双歧杆菌BB536",
        name_en="Bifidobacterium longum BB536",
        category=ConceptCategory.PROBIOTIC,
        aliases=["BB536", "长双歧杆菌BB536", "Bifidobacterium longum BB536"],
        parent_id="bifidobacterium_longum",
        description="报道可缓解过敏性鼻炎与湿疹等症状的菌株"
    ),
    "b_infantis_m63": OntologyNode(
        id="b_infantis_m63",
        name_zh="婴儿双歧杆菌M-63",
        name_en="Bifidobacterium longum subsp. infantis M-63",
        category=ConceptCategory.PROBIOTIC,
        aliases=[
            "M-63",
            "婴儿双歧杆菌M-63",
            "Bifidobacterium longum subsp. infantis M-63",
            "Bifidobacterium infantis M-63",
        ],
        parent_id="bifidobacterium_infantis",
        description="报道可改善婴幼儿肠道菌群并缓解过敏症状的菌株"
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
