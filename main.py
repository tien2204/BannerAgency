import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from typing import Dict, Any
import base64
from mimetypes import guess_type

# Load environment variables
load_dotenv()

class BannerAgent:
    def __init__(self, model_name="gpt-5-nano"):
        llm_kwargs = {
        "model": model_name,
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "max_retries": 3,
        "max_completion_tokens": 4000
        }

        self.llm = ChatOpenAI(**llm_kwargs)
        self.load_prompts()
    
    def load_prompts(self):
        """Load all system prompts"""
        try:
            from prompts.strategist_prompt import strategist_system_prompt
            from prompts.background_designer_prompt import background_designer_system_prompt, background_designer_context_prompt
            from prompts.foreground_designer_prompt import foreground_designer_system_prompt, foreground_designer_context_prompt
            from prompts.design_reviewer_prompt import system_prompt as reviewer_system_prompt
            from prompts.developer_prompt import developer_prompt
            
            self.prompts = {
                'strategist': strategist_system_prompt,
                'background_designer': background_designer_system_prompt,
                'background_designer_context': background_designer_context_prompt,
                'foreground_designer': foreground_designer_system_prompt,
                'foreground_designer_context': foreground_designer_context_prompt,
                'design_reviewer': reviewer_system_prompt,
                'developer': developer_prompt
            }
            print("✅ Loaded prompts from files")
        except ImportError as e:
            print(f"Warning: Could not load prompts: {e}")
            # Fallback to basic prompts
            self.setup_fallback_prompts()
    
    def setup_fallback_prompts(self):
        """Setup basic fallback prompts if imports fail"""
        self.prompts = {
            'strategist': """You are an expert banner objective setter. When a user requests a banner, consider their requirements and develop high-level objectives for an effective banner that would:
- Support the banner's primary purpose
- Create appropriate mood and tone  
- Appeal to the target audience

Analyze the request and provide:
1. Primary Purpose (brand awareness, lead generation, sales, event promotion)
2. Target Audience (demographics, interests, behavior)
3. Mood and Tone (professional, playful, urgent, luxurious, etc.)""",

            'background_designer': """You are an image director specialized in banner backgrounds. Your goal is to create a nice background canvas for foreground elements to be placed. 

When creating the supporting background image, you should:
1. Analyze and consider the provided objectives, user requirements, and provided logo
2. Create a detailed background description considering visual style, mood, color schemes, composition elements, and focal points
3. Focus only on the background's visual and structural elements
4. Avoid mentioning ANY brand/logo names or text elements
5. Ensure the background is free of text elements""",

            'foreground_designer': """You are a textual director specialized in banner layout and typography. Your role is to create precise, varied layouts that follow established design patterns while maintaining visual hierarchy and readability.

Create complete layout specifications with:
1. Typography Hierarchy (headline, subheadline, body text)
2. CTA button design and positioning  
3. Logo placement and sizing
4. Color and contrast considerations
5. Responsive spacing based on banner size
6. Creative and matching font selection""",

            'design_reviewer': """You are an experienced marketing professional in the advertisement industry reviewing a banner ad under development. 
You are iteratively evaluating the foreground elements (text, buttons, etc.) based on their fit with the background.
If the foreground elements are not perfect for production, provide key FEEDBACK on ways to improve. If it looks good overall, approve it.

Focus on:
- Element positioning and overlaps
- Logo placement and visibility  
- Font types, colors, and button design
- Overall professional marketing quality""",

            'developer': """You are a Figma plugin developer. Your tasks:
1. Update ui.html with background and logo image names
2. Follow the JavaScript template
3. Generate and save plugin code with layout implementation
4. Render the image and provide the file path
5. Backup plugin files"""
        }
        print("✅ Using fallback prompts")
    
    def prepare_image_message(self, image_path: str) -> str:
        """Convert image to base64 for API"""
        try:
            mime_type, _ = guess_type(image_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
            
            with open(image_path, "rb") as image_file:
                base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            return f"data:{mime_type};base64,{base64_encoded_data}"
        except Exception as e:
            raise ValueError(f"Failed to process image at {image_path}: {str(e)}")
    
    def strategist_agent(self, user_input: str, logo_path: str = None) -> Dict[str, Any]:
        """
        Strategist agent: Analyzes requirements and sets banner objectives
        """
        print("🎯 Strategist Agent: Analyzing requirements...")
        
        messages = [SystemMessage(content=self.prompts['strategist'])]
        
        content = [{"type": "text", "text": f"Analyze this banner request and provide objectives:\n\nUser request: {user_input}"}]
        
        if logo_path and os.path.exists(logo_path):
            logo_data = self.prepare_image_message(logo_path)
            content.extend([
                {"type": "text", "text": "\nLogo image for reference:"},
                {"type": "image_url", "image_url": {"url": logo_data}}
            ])
        
        messages.append(HumanMessage(content=content))
        
        try:
            response = self.llm.invoke(messages)
            
            # Parse objectives from response
            objectives = self.parse_objectives(response.content)
            
            print(f"✅ Objectives set: {objectives}")
            return objectives
            
        except Exception as e:
            print(f"⚠️ Strategist error: {e}")
            # Return default objectives
            return {
                'purpose': 'Brand Awareness',
                'audience': 'General Public',
                'mood': 'Professional'
            }
    
    def parse_objectives(self, response: str) -> Dict[str, str]:
        """Parse objectives from strategist response"""
        objectives = {
            'purpose': 'Brand Awareness',
            'audience': 'General Public',
            'mood': 'Professional'
        }
        
        # Simple parsing
        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'purpose' in line_lower and ':' in line:
                objectives['purpose'] = line.split(':', 1)[-1].strip()
            elif 'audience' in line_lower and ':' in line:
                objectives['audience'] = line.split(':', 1)[-1].strip()
            elif 'mood' in line_lower or 'tone' in line_lower and ':' in line:
                objectives['mood'] = line.split(':', 1)[-1].strip()
        
        return objectives
    
    def background_designer_agent(self, user_input: str, objectives: Dict[str, Any], 
                                logo_path: str = None, width: int = 1200, height: int = 628) -> str:
        """
        Background Designer Agent: Creates or selects background images
        """
        print("🎨 Background Designer Agent: Working on background...")
        
        # Format context if available
        context_prompt = ""
        if 'background_designer_context' in self.prompts:
            context_prompt = self.prompts['background_designer_context'].format(
                user_input=user_input,
                purpose=objectives.get('purpose', ''),
                audience=objectives.get('audience', ''),
                mood=objectives.get('mood', '')
            )
        
        system_prompt = self.prompts['background_designer'] + "\n\n" + context_prompt
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Create background design description for banner ({width}x{height}px):\n\nRequirements: {user_input}\nObjectives: {objectives}"}]
        
        if logo_path and os.path.exists(logo_path):
            logo_data = self.prepare_image_message(logo_path)
            content.extend([
                {"type": "text", "text": "\nConsider this logo for color compatibility:"},
                {"type": "image_url", "image_url": {"url": logo_data}}
            ])
        
        messages.append(HumanMessage(content=content))
        
        try:
            response = self.llm.invoke(messages)
            print("✅ Background design completed")
            return response.content
        except Exception as e:
            print(f"⚠️ Background designer error: {e}")
            return f"Modern gradient background suitable for {objectives.get('mood', 'professional')} banner"
    
    def foreground_designer_agent(self, user_input: str, objectives: Dict[str, Any],
                                background_description: str, width: int, height: int) -> Dict[str, Any]:
        """
        Foreground Designer Agent: Creates layout and typography specifications
        """
        print("📝 Foreground Designer Agent: Designing layout...")
        
        # Format context if available
        context_prompt = ""
        if 'foreground_designer_context' in self.prompts:
            context_prompt = self.prompts['foreground_designer_context'].format(
                width=width,
                height=height,
                user_input=user_input,
                purpose=objectives.get('purpose', ''),
                audience=objectives.get('audience', ''),
                mood=objectives.get('mood', '')
            )
        
        system_prompt = self.prompts['foreground_designer'] + "\n\n" + context_prompt
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Design foreground layout for {width}x{height}px banner:\n\nRequirements: {user_input}\nObjectives: {objectives}\nBackground: {background_description}\n\nPlease provide specific layout specifications including text content, fonts, sizes, colors, and positions."}]
        
        messages.append(HumanMessage(content=content))
        
        try:
            response = self.llm.invoke(messages)
            
            # Parse layout specifications
            layout_spec = self.parse_layout_specification(response.content, width, height)
            
            print("✅ Foreground layout designed")
            return layout_spec
            
        except Exception as e:
            print(f"⚠️ Foreground designer error: {e}")
            return self.get_fallback_layout(width, height)
    
    def parse_layout_specification(self, response: str, width: int, height: int) -> Dict[str, Any]:
        """Parse layout specification from foreground designer response"""
        # Try to extract structured information from the response
        layout = self.get_fallback_layout(width, height)
        
        # Simple text parsing for common elements
        lines = response.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Look for headline text
            if 'headline' in line_lower and ('text' in line_lower or ':' in line):
                if ':' in line:
                    text = line.split(':', 1)[-1].strip().strip('"\'')
                    if text and len(text) < 100:  # Reasonable headline length
                        layout['headline']['text'] = text
            
            # Look for CTA text
            elif 'cta' in line_lower and ('text' in line_lower or 'button' in line_lower):
                if ':' in line:
                    text = line.split(':', 1)[-1].strip().strip('"\'')
                    if text and len(text) < 30:  # Reasonable CTA length
                        layout['cta']['text'] = text
            
            # Look for colors
            elif '#' in line and len(line.split('#')) > 1:
                color = '#' + line.split('#')[1][:6]
                if len(color) == 7:  # Valid hex color
                    if 'headline' in line_lower:
                        layout['headline']['color'] = color
                    elif 'cta' in line_lower or 'button' in line_lower:
                        layout['cta']['background_color'] = color
        
        return layout
    
    def get_fallback_layout(self, width: int, height: int) -> Dict[str, Any]:
        """Generate fallback layout based on dimensions"""
        # Scale elements based on banner size
        headline_size = max(24, min(width // 20, height // 8))
        subheadline_size = max(16, min(width // 30, height // 12))
        cta_width = max(100, min(width // 6, 200))
        cta_height = max(30, min(height // 12, 50))
        
        return {
            'headline': {
                'text': 'Revolutionary AI Solution',
                'font': 'Arial Bold',
                'size': headline_size,
                'color': '#2C3E50',
                'position': {'x': width // 20, 'y': height // 4},
                'alignment': 'left'
            },
            'subheadline': {
                'text': 'Transform your business with cutting-edge technology',
                'font': 'Arial',
                'size': subheadline_size,
                'color': '#34495E',
                'position': {'x': width // 20, 'y': height // 2},
                'alignment': 'left'
            },
            'cta': {
                'text': 'Get Started',
                'font': 'Arial Bold',
                'size': max(14, subheadline_size - 4),
                'color': '#FFFFFF',
                'background_color': '#3498DB',
                'position': {'x': width // 20, 'y': int(height * 0.75)},
                'width': cta_width,
                'height': cta_height,
                'border_radius': 5
            },
            'logo': {
                'position': {'x': int(width * 0.8), 'y': height // 20},
                'width': max(60, width // 15),
                'height': max(30, height // 20)
            }
        }
    
    def design_reviewer_agent(self, layout_spec: Dict[str, Any],
                            width: int, height: int, iteration: int = 1) -> Dict[str, Any]:
        """
        Design Reviewer Agent: Reviews and provides feedback on the design
        """
        print(f"🔍 Design Reviewer Agent: Reviewing design (iteration {iteration})...")
        
        system_prompt = self.prompts['design_reviewer'].replace('{width}', str(width)).replace('{height}', str(height))
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Review this banner design (iteration {iteration}):\n\nDimensions: {width}x{height}px\n\nLayout specification:\n{json.dumps(layout_spec, indent=2)}\n\nPlease provide feedback on positioning, readability, professional quality, and overall effectiveness."}]
        
        messages.append(HumanMessage(content=content))
        
        try:
            response = self.llm.invoke(messages)
            feedback = self.parse_feedback(response.content)
            
            print(f"✅ Review completed: {len(feedback.get('issues', []))} issues found")
            return feedback
            
        except Exception as e:
            print(f"⚠️ Review error: {e}")
            return {
                'overall_score': 7,
                'issues': [],
                'suggestions': [],
                'approved': iteration >= 2  # Auto-approve after 2 iterations
            }
    
    def parse_feedback(self, response: str) -> Dict[str, Any]:
        """Parse feedback from design reviewer"""
        feedback = {
            'overall_score': 7,
            'issues': [],
            'suggestions': [],
            'approved': False
        }
        
        # Check for approval keywords
        response_lower = response.lower()
        approval_words = ['approve', 'good', 'excellent', 'ready', 'complete']
        feedback['approved'] = any(word in response_lower for word in approval_words)
        
        # Extract issues and suggestions
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            if any(word in line_lower for word in ['issue', 'problem', 'concern', 'error']):
                feedback['issues'].append(line)
            elif any(word in line_lower for word in ['suggest', 'recommend', 'improve', 'consider']):
                feedback['suggestions'].append(line)
        
        return feedback
    
    def create_banner(self, user_input: str, logo_path: str = None, 
                     width: int = 1200, height: int = 628, max_iterations: int = 3) -> str:
        """
        Main method to create a banner ad using the multi-agent system
        """
        print(f"🚀 Starting Banner Creation Process...")
        print(f"📏 Dimensions: {width}x{height}px")
        
        try:
            # Step 1: Strategic Planning
            objectives = self.strategist_agent(user_input, logo_path)
            
            # Step 2: Background Design
            background_description = self.background_designer_agent(
                user_input, objectives, logo_path, width, height
            )
            
            # Step 3: Foreground Design
            layout_spec = self.foreground_designer_agent(
                user_input, objectives, background_description, width, height
            )
            
            # Step 4: Iterative Design Review and Refinement
            current_layout = layout_spec
            for iteration in range(1, max_iterations + 1):
                print(f"\n🔄 Design Iteration {iteration}")
                
                # Review design
                feedback = self.design_reviewer_agent(
                    current_layout, width, height, iteration
                )
                
                if feedback.get('approved', False) or iteration == max_iterations:
                    print(f"✅ Design approved after {iteration} iteration(s)")
                    break
                
                # Refine design based on feedback
                current_layout = self.refine_layout(current_layout, feedback)
            
            # Step 5: Final result
            final_result = {
                'objectives': objectives,
                'background_description': background_description,
                'layout': current_layout,
                'dimensions': {'width': width, 'height': height},
                'iterations': iteration
            }
            
            print("\n🎉 Banner creation completed!")
            return json.dumps(final_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"❌ Error in banner creation: {str(e)}")
            return f"Error: {str(e)}"
    
    def refine_layout(self, layout_spec: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Refine layout based on feedback"""
        refined_layout = json.loads(json.dumps(layout_spec))  # Deep copy
        
        issues = feedback.get('issues', [])
        suggestions = feedback.get('suggestions', [])
        
        for issue in issues + suggestions:
            issue_lower = issue.lower()
            
            # Font size adjustments
            if 'font' in issue_lower and ('size' in issue_lower or 'larger' in issue_lower or 'smaller' in issue_lower):
                for element in ['headline', 'subheadline']:
                    if element in refined_layout:
                        current_size = refined_layout[element].get('size', 24)
                        if 'larger' in issue_lower:
                            refined_layout[element]['size'] = min(current_size * 1.2, 72)
                        elif 'smaller' in issue_lower:
                            refined_layout[element]['size'] = max(current_size * 0.8, 12)
            
            # Position adjustments
            elif 'position' in issue_lower or 'move' in issue_lower:
                for element in refined_layout:
                    if isinstance(refined_layout[element], dict) and 'position' in refined_layout[element]:
                        # Small positional adjustments
                        if 'down' in issue_lower:
                            refined_layout[element]['position']['y'] += 20
                        elif 'up' in issue_lower:
                            refined_layout[element]['position']['y'] = max(10, refined_layout[element]['position']['y'] - 20)
                        elif 'right' in issue_lower:
                            refined_layout[element]['position']['x'] += 20
                        elif 'left' in issue_lower:
                            refined_layout[element]['position']['x'] = max(10, refined_layout[element]['position']['x'] - 20)
            
            # CTA improvements
            elif 'cta' in issue_lower or 'button' in issue_lower:
                if 'cta' in refined_layout:
                    if 'larger' in issue_lower:
                        refined_layout['cta']['width'] = min(refined_layout['cta'].get('width', 120) * 1.3, 250)
                        refined_layout['cta']['height'] = min(refined_layout['cta'].get('height', 40) * 1.2, 60)
                    elif 'prominent' in issue_lower or 'visible' in issue_lower:
                        refined_layout['cta']['background_color'] = '#E74C3C'  # More prominent red
        
        return refined_layout

def main():
    """Example usage"""
    # Initialize the agent
    agent = BannerAgent(model_name="gpt-5-nano")
    
    # Example banner request
    user_request = "Create a banner for a tech startup launching a new AI product. The banner should be modern, professional, and appeal to business executives."
    logo_path = "./logos/example_logo.png"  # Optional
    
    # Create banner
    result = agent.create_banner(
        user_input=user_request,
        logo_path=logo_path if os.path.exists(logo_path) else None,
        width=1200,
        height=628,
        max_iterations=3
    )
    
    print("\n📄 Final Banner Specification:")
    print(result)

if __name__ == "__main__":
    main()