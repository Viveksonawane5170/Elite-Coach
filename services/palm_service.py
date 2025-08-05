import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini
GEMINI_AVAILABLE = False
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

def generate_coaching_prompt(user_profile):
    if not GEMINI_AVAILABLE:
        return generate_fallback_response(user_profile)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Create a comprehensive {user_profile['sport']} training plan for a {user_profile['level']} athlete with these goals: {', '.join(user_profile['goals'])}.
        
        Structure the response EXACTLY as follows:

        <div class='coaching-plan'>
        <div class='plan-header'>
        <h2>{user_profile['sport'].title()} Performance Blueprint</h2>
        <h3>For {user_profile['level'].title()} Level Athletes</h3>
        </div>

        <div class='motivation-section'>
        <h4>Mindset Preparation</h4>
        <p><strong>Key Motivation:</strong> [2-3 sentence inspiring message]</p>
        <p><strong>Performance Focus:</strong> [Main area to concentrate on]</p>
        </div>

        <div class='weekly-plan'>
        <h4>8-Week Training Structure</h4>
        <div class='week-section'>
        <h5>Week 1-2: Foundation Phase</h5>
        <p><strong>Monday - Technique Development:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Tuesday - Endurance Building:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Wednesday - Active Recovery:</strong> [Detailed activities including mobility work, foam rolling, and light cardio]</p>
        <p><strong>Thursday - Strength & Power:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Friday - Skill Refinement:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Saturday - Long Duration Session:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Sunday - Complete Rest:</strong> Mental recovery and preparation for next week</p>
        </div>

        <div class='week-section'>
        <h5>Week 3-4: Build Phase</h5>
        <p><strong>Monday - Advanced Technique:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Tuesday - High-Intensity Intervals:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Wednesday - Active Recovery & Mobility:</strong> [Detailed activities including yoga, foam rolling, and light swimming]</p>
        <p><strong>Thursday - Strength & Power:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Friday - Competition Simulation:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Saturday - Progressive Overload Session:</strong> [Detailed workout including warm-up, main sets, cool-down, duration, and specific focus]</p>
        <p><strong>Sunday - Active Recovery:</strong> Light cross-training and mental preparation</p>
        </div>
        
        <div class='week-section'>
        <h5>Week 5-6: Intensity Phase</h5>
        [Same detailed structure...]
        </div>
        
        <div class='week-section'>
        <h5>Week 7-8: Peak Performance Phase</h5>
        [Same detailed structure...]
        </div>
        </div>

        <div class='technical-section'>
        <h4>Technical Excellence</h4>
        <p><strong>Key Drill:</strong> [Specific drill with step-by-step instructions]</p>
        <p><strong>Game-Specific Techniques:</strong> [3-5 sport-specific technical tips for in-game situations]</p>
        <p><strong>Tactical Insights:</strong> [Positioning strategies and decision-making guidance]</p>
        <p><strong>Common Mistakes:</strong> [Frequent errors and how to correct them]</p>
        <p><strong>Equipment Optimization:</strong> [Specific guidance on gear selection and usage]</p>
        </div>

        <div class='recovery-section'>
        <h4>Optimal Recovery Protocol</h4>
        <p><strong>Active Recovery:</strong> [Detailed recommendations including specific exercises and durations]</p>
        <p><strong>Nutrition:</strong> [Specific meal timing, macro ratios, and hydration strategies]</p>
        <p><strong>Sleep Protocol:</strong> [Optimal sleep duration and quality enhancement techniques]</p>
        <p><strong>Injury Prevention:</strong> [Specific exercises and warning signs to monitor]</p>
        </div>
        
        <div class='progress-tracking'>
        <h4>Performance Metrics Tracking</h4>
        <p><strong>Weekly Assessments:</strong> [Specific metrics to track each week]</p>
        <p><strong>Key Performance Indicators:</strong> [Benchmarks for success at each phase]</p>
        </div>
        </div>

        Use a {user_profile['preferences']['motivational_style']} tone and {user_profile['preferences']['length']} length.
        Include:
        - Exact durations, distances, weights, and intensities
        - Specific exercise names and descriptions
        - Progressive overload principles
        - Periodization details
        - Sport-specific technical cues
        
        For the Technical Excellence section:
        - Provide 3-5 specific game techniques relevant to {user_profile['sport']}
        - Include tactical positioning advice for different game situations
        - List common mistakes and their corrections
        - Add sport-specific equipment tips
        """
        
        response = model.generate_content(prompt)
        return format_response(response.text, user_profile)
    except Exception as e:
        print(f"Gemini generation failed: {e}")
        return generate_fallback_response(user_profile)

def format_response(response, user_profile):
    """Format the response with proper HTML structure"""
    # Clean up markdown artifacts
    cleaned_response = (
        response
        .replace('*', '')
        .replace('#', '')
        .replace('**', '')
        .replace('__', '')
    )
    
    # Convert to proper HTML paragraphs
    formatted_paragraphs = [
        f"<p>{line}</p>" if not line.startswith('<') else line
        for line in cleaned_response.split('\n')
        if line.strip()
    ]
    
    return f"""
    <div class='coaching-plan {user_profile["sport"]}-plan {user_profile["level"]}-level'>
        {"".join(formatted_paragraphs)}
    </div>
    """

def generate_fallback_response(user_profile):
    """Structured fallback response with enhanced technical section"""
    sport = user_profile['sport'].lower()
    technical_tips = {
        'basketball': [
            "Triple threat positioning: Always be ready to shoot, pass, or dribble",
            "Defensive stance: Stay low with wide base and active hands",
            "Boxing out: Seal defenders immediately after shot release"
        ],
        'soccer': [
            "First touch: Direct ball away from pressure into space",
            "Body positioning: Shield ball using arm and body awareness",
            "Passing lanes: Cut angles with proper positioning"
        ],
        'tennis': [
            "Split step: Time your jump with opponent's contact",
            "Court positioning: Recover to center after each shot",
            "Shot selection: Choose high-percentage shots based on position"
        ],
        'swimming': [
            "Streamlining: Tight core and extended arms off walls",
            "Breathing timing: Exhale underwater, quick inhale",
            "Pace judgment: Negative split race strategy"
        ],
        'default': [
            "Anticipation: Read opponent's body language early",
            "Efficient movement: Minimize unnecessary steps",
            "Situational awareness: Understand game context at all times"
        ]
    }
    
    tips = technical_tips.get(sport, technical_tips['default'])
    tips_html = "".join([f"<li>{tip}</li>" for tip in tips])
    
    return f"""
    <div class='coaching-plan'>
        <div class='plan-header'>
            <h2>{user_profile['sport'].title()} Training Plan</h2>
            <h3>For {user_profile['level'].title()} Athletes</h3>
        </div>
        
        <div class='motivation-section'>
            <h4>General Guidance</h4>
            <p><strong>Key Focus:</strong> Consistent practice on {', '.join(user_profile['goals'])}</p>
            <p><strong>Weekly Structure:</strong> 
            <strong>Mon:</strong> Technique, 
            <strong>Tue:</strong> Endurance, 
            <strong>Wed:</strong> Recovery, 
            <strong>Thu:</strong> Strength, 
            <strong>Fri:</strong> Skills, 
            <strong>Sat:</strong> Long Session, 
            <strong>Sun:</strong> Rest</p>
        </div>
        
        <div class='technical-section'>
            <h4>Technical Excellence</h4>
            <p><strong>Key Drill:</strong> Sport-specific fundamental drill</p>
            <p><strong>Game-Specific Techniques:</strong></p>
            <ul>{tips_html}</ul>
            <p><strong>Tactical Insights:</strong> Position yourself according to game situation</p>
            <p><strong>Common Mistakes:</strong> Avoid overcomplicating plays under pressure</p>
            <p><strong>Equipment Optimization:</strong> Ensure proper gear fit and maintenance</p>
        </div>
        
        <div class='recovery-section'>
            <h4>Recovery Protocol</h4>
            <p><strong>Daily:</strong> 8 hours sleep, hydration (35ml/kg body weight)</p>
            <p><strong>Post-workout:</strong> 3:1 carb-to-protein ratio within 30 minutes</p>
        </div>
    </div>
    """