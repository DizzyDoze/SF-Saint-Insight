# Classroom whiteboard analysis prompts
DEFAULT_PROMPT = """
Analyze this whiteboard image from a classroom setting. Focus on:

1. Mathematical equations, formulas, or expressions - explain their meaning and applications
2. Scientific diagrams or charts - describe what they represent
3. Key concepts, definitions, or terminology - provide clear explanations suitable for students
4. Any step-by-step procedures or problem-solving methods

If you see partial writing or unclear content, make reasonable inferences.
Use student-friendly language and explain concepts at an appropriate level.
Keep explanations clear, concise, and focused on helping students understand the material.
"""

# Subject-specific prompts
MATH_PROMPT = """
Analyze this mathematics whiteboard image. Focus on:

1. Identify and explain equations, formulas, and mathematical expressions
2. For problem-solving steps, explain the logic behind each step
3. Highlight key mathematical concepts and theorems being used
4. Provide context about where these concepts are applied

Explain in clear, student-friendly language with proper mathematical terminology.
"""

SCIENCE_PROMPT = """
Analyze this science whiteboard image. Focus on:

1. Identify scientific diagrams, processes, or experimental setups
2. Explain scientific terminology, concepts, and principles
3. Describe relationships between concepts and how they connect
4. Highlight any formulas and explain their scientific significance

Use appropriate scientific terminology while keeping explanations accessible to students.
"""

HUMANITIES_PROMPT = """
Analyze this humanities whiteboard image. Focus on:

1. Identify key concepts, timelines, or frameworks being discussed
2. Explain any terminology, names, or significant events
3. Highlight connections between ideas or historical contexts
4. Summarize main themes or arguments presented

Provide clear explanations that help students understand the broader context and significance.
"""

# Application settings
APP_SETTINGS = {
    "analyze_interval": 5,  # Seconds between analyses
    "confidence_threshold": 0.3,  # YOLO detection confidence threshold
    "max_regions": 2,  # Maximum regions to analyze per frame
    "model": "gemini-2.0-flash"  # Default Gemini model
}