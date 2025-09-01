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
        """Initialize the BannerAgent with GPT-5-nano"""
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
            max_tokens=4000,
            max_retries=3,
        )
        
        # Load prompts from the provided prompt files
        self.load_prompts()
    
    def load_prompts(self):
        """Load all system prompts"""
        # Import the prompt modules (assuming they're in the prompts directory)
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
        except ImportError as e:
            print(f"Warning: Could not load prompts: {e}")
            # Fallback to basic prompts
            self.setup_fallback_prompts()
    
    def setup_fallback_prompts(self):
        """Setup basic fallback prompts if imports fail"""
        self.prompts = {
            'strategist': "You are an expert banner objective setter. Analyze user requirements and create banner objectives.",
            'background_designer': "You are an image director specialized in banner backgrounds.",
            'foreground_designer': "You are a textual director specialized in banner layout and typography.",
            'design_reviewer': "You are an experienced marketing professional reviewing banner ads.",
            'developer': "You are a Figma plugin developer for banner implementation."
        }
    
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
        
        content = [{"type": "text", "text": f"User request: {user_input}"}]
        
        if logo_path and os.path.exists(logo_path):
            logo_data = self.prepare_image_message(logo_path)
            content.extend([
                {"type": "text", "text": "Logo image:"},
                {"type": "image_url", "image_url": {"url": logo_data}}
            ])
        
        messages.append(HumanMessage(content=content))
        
        response = self.llm.invoke(messages)
        
        # Parse objectives from response
        objectives = self.parse_objectives(response.content)
        
        print(f"✅ Objectives set: {objectives}")
        return objectives
    
    def parse_objectives(self, response: str) -> Dict[str, str]:
        """Parse objectives from strategist response"""
        # Simple parsing - in production, you might want more sophisticated parsing
        lines = response.split('\n')
        objectives = {
            'purpose': 'Brand Awareness',
            'audience': 'General Public',
            'mood': 'Professional'
        }
        
        for line in lines:
            if 'purpose' in line.lower():
                objectives['purpose'] = line.split(':', 1)[-1].strip()
            elif 'audience' in line.lower():
                objectives['audience'] = line.split(':', 1)[-1].strip()
            elif 'mood' in line.lower():
                objectives['mood'] = line.split(':', 1)[-1].strip()
        
        return objectives
    
    def background_designer_agent(self, user_input: str, objectives: Dict[str, Any], 
                                logo_path: str = None, width: int = 1200, height: int = 628) -> str:
        """
        Background Designer Agent: Creates or selects background images
        """
        print("🎨 Background Designer Agent: Working on background...")
        
        # Format context prompt
        context = self.prompts.get('background_designer_context', '').format(
            user_input=user_input,
            purpose=objectives.get('purpose', ''),
            audience=objectives.get('audience', ''),
            mood=objectives.get('mood', '')
        )
        
        system_prompt = self.prompts['background_designer'] + context
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Create background for banner ({width}x{height}px)"}]
        
        if logo_path and os.path.exists(logo_path):
            logo_data = self.prepare_image_message(logo_path)
            content.extend([
                {"type": "text", "text": "Consider this logo:"},
                {"type": "image_url", "image_url": {"url": logo_data}}
            ])
        
        messages.append(HumanMessage(content=content))
        
        response = self.llm.invoke(messages)
        
        print("✅ Background design completed")
        return response.content
    
    def foreground_designer_agent(self, user_input: str, objectives: Dict[str, Any],
                                background_path: str, width: int, height: int) -> Dict[str, Any]:
        """
        Foreground Designer Agent: Creates layout and typography specifications
        """
        print("📝 Foreground Designer Agent: Designing layout...")
        
        # Format context prompt
        context = self.prompts.get('foreground_designer_context', '').format(
            width=width,
            height=height,
            user_input=user_input,
            purpose=objectives.get('purpose', ''),
            audience=objectives.get('audience', ''),
            mood=objectives.get('mood', '')
        )
        
        system_prompt = self.prompts['foreground_designer'] + context
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Design foreground layout for {width}x{height}px banner"}]
        
        if background_path and os.path.exists(background_path):
            bg_data = self.prepare_image_message(background_path)
            content.extend([
                {"type": "text", "text": "Background image:"},
                {"type": "image_url", "image_url": {"url": bg_data}}
            ])
        
        messages.append(HumanMessage(content=content))
        
        response = self.llm.invoke(messages)
        
        # Parse layout specifications
        layout_spec = self.parse_layout_specification(response.content)
        
        print("✅ Foreground layout designed")
        return layout_spec
    
    def parse_layout_specification(self, response: str) -> Dict[str, Any]:
        """Parse layout specification from foreground designer response"""
        # This is a simplified parser - you might want to implement more sophisticated parsing
        layout = {
            'headline': {
                'text': 'Your Brand Message',
                'font': 'Arial',
                'size': 48,
                'color': '#000000',
                'position': {'x': 50, 'y': 100}
            },
            'subheadline': {
                'text': 'Supporting message',
                'font': 'Arial',
                'size': 24,
                'color': '#333333',
                'position': {'x': 50, 'y': 160}
            },
            'cta': {
                'text': 'Learn More',
                'font': 'Arial',
                'size': 18,
                'color': '#FFFFFF',
                'background_color': '#007BFF',
                'position': {'x': 50, 'y': 220},
                'width': 120,
                'height': 40
            },
            'logo': {
                'position': {'x': 50, 'y': 50},
                'width': 100,
                'height': 50
            }
        }
        
        return layout
    
    def design_reviewer_agent(self, rendered_image_path: str, layout_spec: Dict[str, Any],
                            width: int, height: int, iteration: int = 1) -> Dict[str, Any]:
        """
        Design Reviewer Agent: Reviews and provides feedback on the design
        """
        print(f"🔍 Design Reviewer Agent: Reviewing design (iteration {iteration})...")
        
        system_prompt = self.prompts['design_reviewer'].format(width=width, height=height)
        messages = [SystemMessage(content=system_prompt)]
        
        content = [{"type": "text", "text": f"Review this banner design (iteration {iteration}):"}]
        
        if rendered_image_path and os.path.exists(rendered_image_path):
            image_data = self.prepare_image_message(rendered_image_path)
            content.extend([
                {"type": "text", "text": "Rendered banner:"},
                {"type": "image_url", "image_url": {"url": image_data}},
                {"type": "text", "text": f"Layout specification: {json.dumps(layout_spec, indent=2)}"}
            ])
        
        messages.append(HumanMessage(content=content))
        
        response = self.llm.invoke(messages)
        
        feedback = self.parse_feedback(response.content)
        
        print(f"✅ Review completed: {len(feedback.get('issues', []))} issues found")
        return feedback
    
    def parse_feedback(self, response: str) -> Dict[str, Any]:
        """Parse feedback from design reviewer"""
        # Simple parsing - in production, implement more sophisticated parsing
        feedback = {
            'overall_score': 7,  # Default score
            'issues': [],
            'suggestions': [],
            'approved': 'good' in response.lower() or 'excellent' in response.lower()
        }
        
        lines = response.split('\n')
        for line in lines:
            if 'issue' in line.lower() or 'problem' in line.lower():
                feedback['issues'].append(line.strip())
            elif 'suggest' in line.lower() or 'recommend' in line.lower():
                feedback['suggestions'].append(line.strip())
        
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
            background_design = self.background_designer_agent(
                user_input, objectives, logo_path, width, height
            )
            
            # Step 3: Foreground Design
            layout_spec = self.foreground_designer_agent(
                user_input, objectives, None, width, height
            )
            
            # Step 4: Iterative Design Review and Refinement
            current_layout = layout_spec
            for iteration in range(1, max_iterations + 1):
                print(f"\n🔄 Design Iteration {iteration}")
                
                # Simulate rendering (in production, this would call the developer agent)
                rendered_path = f"./rendered/banner_iteration_{iteration}.png"
                
                # Review design
                feedback = self.design_reviewer_agent(
                    None, current_layout, width, height, iteration
                )
                
                if feedback.get('approved', False) or iteration == max_iterations:
                    print(f"✅ Design approved after {iteration} iteration(s)")
                    break
                
                # Refine design based on feedback
                current_layout = self.refine_layout(current_layout, feedback)
            
            print("\n🎉 Banner creation completed!")
            return json.dumps(current_layout, indent=2)
            
        except Exception as e:
            print(f"❌ Error in banner creation: {str(e)}")
            return f"Error: {str(e)}"
    
    def refine_layout(self, layout_spec: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Refine layout based on feedback"""
        # Simple refinement logic - in production, this would use the foreground designer agent
        refined_layout = layout_spec.copy()
        
        # Example refinements based on common feedback
        issues = feedback.get('issues', [])
        for issue in issues:
            if 'font size' in issue.lower():
                # Adjust font sizes
                for element in ['headline', 'subheadline']:
                    if element in refined_layout:
                        refined_layout[element]['size'] = min(
                            refined_layout[element]['size'] * 1.1, 72
                        )
            elif 'position' in issue.lower():
                # Adjust positions slightly
                for element in refined_layout:
                    if 'position' in refined_layout[element]:
                        refined_layout[element]['position']['x'] += 10
        
        return refined_layout

def main():
    """Example usage"""
    # Initialize the agent
    agent = BannerAgent()
    
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
    
    print("\n📄 Final Layout Specification:")
    print(result)

if __name__ == "__main__":
    main()
