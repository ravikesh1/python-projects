"""Sample medical/health documents and structured patient records for comparison."""

DOCUMENTS = [
    {
        "id": "doc1",
        "text": "Heart attacks occur when blood flow to the heart is blocked. Symptoms include chest pain, shortness of breath, and nausea.",
        "metadata": {"category": "cardiology", "severity": "critical"},
    },
    {
        "id": "doc2",
        "text": "Diabetes is a chronic condition where the body cannot properly process blood sugar. Type 2 diabetes is the most common form.",
        "metadata": {"category": "endocrinology", "severity": "chronic"},
    },
    {
        "id": "doc3",
        "text": "Migraine headaches cause intense throbbing pain, usually on one side of the head. Triggers include stress, bright lights, and certain foods.",
        "metadata": {"category": "neurology", "severity": "moderate"},
    },
    {
        "id": "doc4",
        "text": "High blood pressure often has no symptoms but increases the risk of heart disease and stroke. Regular monitoring is essential.",
        "metadata": {"category": "cardiology", "severity": "chronic"},
    },
    {
        "id": "doc5",
        "text": "Asthma is a respiratory condition causing difficulty breathing, wheezing, and coughing. Inhalers provide quick relief during attacks.",
        "metadata": {"category": "pulmonology", "severity": "moderate"},
    },
    {
        "id": "doc6",
        "text": "Anxiety disorders involve excessive worry and fear. Cognitive behavioral therapy and medication are common treatments.",
        "metadata": {"category": "psychiatry", "severity": "moderate"},
    },
    {
        "id": "doc7",
        "text": "Broken bones require immobilization with a cast or splint. Severe fractures may need surgical repair with metal plates or screws.",
        "metadata": {"category": "orthopedics", "severity": "acute"},
    },
    {
        "id": "doc8",
        "text": "Pneumonia is a lung infection causing cough, fever, and difficulty breathing. Bacterial pneumonia is treated with antibiotics.",
        "metadata": {"category": "pulmonology", "severity": "critical"},
    },
]

PATIENTS = [
    {"name": "Alice Johnson", "age": 45, "condition": "hypertension", "department": "cardiology", "status": "active"},
    {"name": "Bob Smith", "age": 62, "condition": "type 2 diabetes", "department": "endocrinology", "status": "active"},
    {"name": "Carol Davis", "age": 34, "condition": "migraine", "department": "neurology", "status": "active"},
    {"name": "David Wilson", "age": 58, "condition": "coronary artery disease", "department": "cardiology", "status": "active"},
    {"name": "Eve Martinez", "age": 28, "condition": "asthma", "department": "pulmonology", "status": "discharged"},
    {"name": "Frank Lee", "age": 41, "condition": "generalized anxiety", "department": "psychiatry", "status": "active"},
    {"name": "Grace Kim", "age": 55, "condition": "pneumonia", "department": "pulmonology", "status": "active"},
    {"name": "Henry Patel", "age": 37, "condition": "fractured tibia", "department": "orthopedics", "status": "discharged"},
]
