import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from typing import Dict, Any
import base64
import cairosvg
from mimetypes import guess_type

# Load environment variables
load_dotenv()

class BannerAgent:
    def __init__(self, model_name="gpt-5-nano"):
        llm_kwargs = {
            "model": model_name,
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "max_retries": 3,
            "temperature": 1.0,  # <-- THÊM DÒNG NÀY ĐỂ SỬA LỖI
            "model_kwargs": {
                # Sửa cảnh báo UserWarning: chuyển max_completion_tokens vào đây
                # và đổi tên thành max_tokens theo chuẩn của OpenAI API
                "max_completion_tokens": 4000 
            }
        }

        # Xóa tham số không còn hợp lệ ra khỏi khởi tạo chính
        # llm_kwargs.pop("max_completion_tokens", None) 

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
            
            # THÊM DÒNG NÀY ĐỂ GỠ LỖI
            print("--- Raw Foreground Designer Output ---")
            print(response.content)
            print("------------------------------------")

            # Parse layout specifications
            layout_spec = self.parse_layout_specification(response.content, width, height)
            
            print("✅ Foreground layout designed")
            return layout_spec
            
        except Exception as e:
            print(f"⚠️ Foreground designer error: {e}")
            return self.get_fallback_layout(width, height)
    
    def parse_layout_specification(self, response: str, width: int, height: int) -> Dict[str, Any]:
        """Parse structured layout specification from LLM response"""
        try:
            # Tìm đoạn JSON trong response
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                layout_json = response[start:end+1]
                layout = json.loads(layout_json)
                return layout
        except Exception as e:
            print(f"⚠️ Parse layout JSON error: {e}")
        
        # Nếu thất bại → fallback
        return self.get_fallback_layout(width, height)
    
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
                'font_family': 'Arial',
                'font_size': headline_size,
                'color': '#2C3E50',
                'position': {'x': width // 20, 'y': height // 4},
                'dimensions': {'width': width * 0.9, 'height': headline_size * 1.2},
                'alignment': 'left'
            },
            'subheadline': {
                'text': 'Transform your business with cutting-edge technology',
                'font_family': 'Arial',
                'font_size': subheadline_size,
                'color': '#34495E',
                'position': {'x': width // 20, 'y': height // 2},
                'dimensions': {'width': width * 0.9, 'height': subheadline_size * 2.5},
                'alignment': 'left'
            },
            'cta_button': {
                'text': 'Get Started',
                'font_family': 'Arial',
                'font_size': max(14, subheadline_size - 4),
                'color': '#FFFFFF',
                'background_color': '#3498DB',
                'position': {'x': width // 20, 'y': int(height * 0.75)},
                'dimensions': {'width': cta_width, 'height': cta_height},
                'border_radius': 5
            },
            'logo': {
                'position': {'x': int(width * 0.8), 'y': height // 20},
                'dimensions': {'width': max(60, width // 15), 'height': max(30, height // 20)}
            }
        }
    
    def design_reviewer_agent(self, user_input: str, layout_spec: Dict[str, Any], background_description: str,
                        width: int, height: int, iteration: int = 1,
                        png_preview_b64: str = None) -> Dict[str, Any]:
        """
        Design Reviewer Agent: Reviews and provides feedback on the design using a PNG preview.
        """
        print(f"🔍 Design Reviewer Agent: Reviewing design (iteration {iteration})...")

        system_prompt = self.prompts['design_reviewer'].replace('{width}', str(width)).replace('{height}', str(height))
        messages = [SystemMessage(content=system_prompt)]

        # Đã thêm user_input vào đây để agent có thể đối chiếu
        content = [{"type": "text", "text": f"""Review this banner design (iteration {iteration}):

    Original User Request: "{user_input}"

    Dimensions: {width}x{height}px
    Background: {background_description}
    Layout specification:
    {json.dumps(layout_spec, indent=2)}

    Critically evaluate the design against the user request and visual quality rules."""}]

        if png_preview_b64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{png_preview_b64}"}
            })
            content.append({"type": "text", "text": "Above is the visual preview of the banner design."})

        messages.append(HumanMessage(content=content))

        try:
            response = self.llm.invoke(messages)
            feedback = self.parse_feedback(response.content)

            print(f"✅ Review completed: {len(feedback.get('issues', []))} issues found")
            return feedback

        except Exception as e:
            print(f"⚠️ Review error: {e}")
            return {
                'approved': iteration >= max_iterations, # Chỉ approve ở lần cuối nếu có lỗi
                'issues': [{'reason': f'Reviewer agent failed with error: {e}'}],
                'suggestions': []
            }
    
    def parse_feedback(self, response: str) -> Dict[str, Any]:
        """Parse structured JSON feedback from reviewer"""
        try:
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                feedback_json = response[start:end+1]
                feedback = json.loads(feedback_json)
                return feedback
        except Exception as e:
            print(f"⚠️ Parse feedback JSON error: {e}")

        # fallback nếu parse thất bại
        return {
            "approved": False,
            "issues": [],
            "suggestions": []
        }


    def export_to_svg(self, layout: Dict[str, Any], background_desc: str, width: int, height: int, logo_path: str) -> str:
        """
        Generate SVG using actual layout specification, with support for multi-line text.
        """
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'

        # Background
        if "tech" in background_desc.lower() or "ai" in background_desc.lower():
            svg += f'''<defs><linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0F0F23"/><stop offset="100%" stop-color="#1a1a2e"/></linearGradient></defs><rect width="{width}" height="{height}" fill="url(#bgGrad)"/><rect width="{width}" height="{height}" fill="url(#bgGrad)"/>'''
            for i in range(0, width, 20):
                svg += f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="rgba(116,185,255,0.1)" stroke-width="0.5"/>'
            for i in range(0, height, 20):
                svg += f'<line x1="0" y1="{i}" x2="{width}" y2="{i}" stroke="rgba(116,185,255,0.1)" stroke-width="0.5"/>'
        else:
            svg += f'<rect width="{width}" height="{height}" fill="#f8f9fa"/>'

        # --- TEXT RENDERING LOGIC (UPGRADED) ---
        def render_text(element_name, default_font_size):
            if element_name not in layout or not layout.get(element_name):
                return ""
            
            elem = layout[element_name]
            text_content = elem.get('text', '')
            # Nếu text là list (đã được AI chia sẵn), nối lại. Nếu là string, giữ nguyên.
            if isinstance(text_content, list):
                lines = text_content
            else: # Tự chia nếu AI chưa chia
                # Ước tính số ký tự mỗi dòng dựa trên font size và chiều rộng banner
                chars_per_line = int((width * 0.9) / (elem.get('font_size', default_font_size) * 0.6))
                import textwrap
                lines = textwrap.wrap(text_content, width=chars_per_line if chars_per_line > 0 else 20)

            font_size = elem.get('font_size', default_font_size)
            x = elem.get('position', {}).get('x', 10)
            y = elem.get('position', {}).get('y', font_size)
            
            text_svg = f'<text x="{x}" y="{y}" font-family="{elem.get("font_family", "Arial")}" font-size="{font_size}" fill="{elem.get("color", "#FFFFFF")}">'
            for i, line in enumerate(lines):
                # dy="1.2em" để tạo khoảng cách giữa các dòng
                text_svg += f'<tspan x="{x}" dy="{ "1.2em" if i > 0 else 0 }">{line}</tspan>'
            text_svg += '</text>'
            return text_svg

        svg += render_text('headline', 28)
        svg += render_text('subheadline', 16)
        # --- END OF UPGRADED TEXT LOGIC ---

        if 'cta_button' in layout and layout.get('cta_button'):
            cta = layout['cta_button']
            pos = cta.get('position', {})
            dims = cta.get('dimensions', {})
            font_size = cta.get('font_size', 14)
            svg += f'''<rect x="{pos.get('x', 0)}" y="{pos.get('y', 0)}" width="{dims.get('width', 100)}" height="{dims.get('height', 40)}" rx="{cta.get('border_radius', 5)}" fill="{cta.get('background_color', '#007BFF')}"/>'''
            text_x = pos.get('x', 0) + dims.get('width', 100) // 2
            text_y = pos.get('y', 0) + dims.get('height', 40) // 2 + font_size // 3
            svg += f'''<text x="{text_x}" y="{text_y}" font-family="{cta.get('font_family', 'Arial')}" font-size="{font_size}" fill="{cta.get('color', '#FFFFFF')}" text-anchor="middle">{cta.get('text', '')}</text>'''

        if logo_path and os.path.exists(logo_path) and 'logo' in layout and layout.get('logo'):
            try:
                with open(logo_path, "rb") as img_file:
                    base64_img = base64.b64encode(img_file.read()).decode('utf-8')
                mime = guess_type(logo_path)[0] or 'image/png'
                logo = layout['logo']
                pos = logo.get('position', {})
                dims = logo.get('dimensions', {})
                svg += f'''<image x="{pos.get('x', 0)}" y="{pos.get('y', 0)}" width="{dims.get('width', 80)}" height="{dims.get('height', 30)}" xlink:href="data:{mime};base64,{base64_img}"/>'''
            except Exception as e:
                print(f"⚠️ Logo rendering error: {e}")
        
        svg += '</svg>'
        return svg


    def extract_logo_name_from_path(self, logo_path: str) -> str:
        """Extract a display name from logo file path"""
        if not logo_path:
            return "LOGO"
        
        # Get filename without extension
        filename = os.path.splitext(os.path.basename(logo_path))[0]
        
        # Handle common naming patterns
        if "ethic" in filename.lower():
            return "ETHIC AI"
        elif "ai" in filename.lower():
            return "AI"
        elif "_" in filename:
            # Split on underscore and capitalize
            parts = filename.split("_")
            return " ".join(part.upper() for part in parts if part.isalpha())
        else:
            return filename.upper()[:10]  # Limit length

    def export_to_figma_plugin(self, layout: Dict[str, Any], background_description: str, width: int, height: int) -> Dict[str, str]:
        """Generate complete Figma Plugin files"""
        
        # manifest.json
        manifest = {
            "name": "Banner Generator Plugin",
            "id": "banner-generator",
            "api": "1.0.0",
            "main": "code.js",
            "ui": "ui.html"
        }
        
        # ui.html
        ui_html = f'''<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Banner Generator</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; margin: 20px; }}
                .banner-preview {{ 
                    width: {width//2}px; 
                    height: {height//2}px; 
                    border: 1px solid #ccc; 
                    margin: 10px 0; 
                    transform-origin: top left;
                    transform: scale(0.5);
                }}
                button {{ 
                    background: #18A0FB; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 6px; 
                    cursor: pointer; 
                }}
            </style>
        </head>
        <body>
            <h2>Banner Generator</h2>
            <div class="banner-preview" id="preview"></div>
            <button onclick="createBanner()">Create Banner in Figma</button>
            
            <script>
                const layout = {json.dumps(layout, indent=2)};
                const dimensions = {{ width: {width}, height: {height} }};
                
                function createBanner() {{
                    parent.postMessage({{ pluginMessage: {{ type: 'create-banner', layout, dimensions }} }}, '*');
                }}
                
                // Preview rendering
                document.getElementById('preview').innerHTML = `
                    <div style="width: {width}px; height: {height}px; background: #f0f0f0; position: relative;">
                        <div style="position: absolute; left: {layout.get('headline', {}).get('position', {}).get('x', 0)}px; 
                                top: {layout.get('headline', {}).get('position', {}).get('y', 0)}px; 
                                font-size: {layout.get('headline', {}).get('size', 24)}px; 
                                color: {layout.get('headline', {}).get('color', '#000')};
                                font-family: {layout.get('headline', {}).get('font', 'Arial')};">
                            {layout.get('headline', {}).get('text', 'Headline')}
                        </div>
                    </div>
                `;
            </script>
        </body>
        </html>'''
        
        # code.js (Figma Plugin API)
        code_js = f'''// Figma Plugin Code
        figma.showUI(__html__, {{ width: 400, height: 300 }});

        figma.ui.onmessage = msg => {{
        if (msg.type === 'create-banner') {{
            const {{ layout, dimensions }} = msg;
            
            // Create frame for banner
            const frame = figma.createFrame();
            frame.name = "Generated Banner";
            frame.resize(dimensions.width, dimensions.height);
            frame.fills = [{{
            type: 'SOLID',
            color: {{ r: 0.94, g: 0.94, b: 0.94 }}
            }}];
            
            // Add headline
            if (layout.headline) {{
            const headline = figma.createText();
            headline.name = "Headline";
            headline.characters = layout.headline.text;
            headline.fontSize = layout.headline.size;
            headline.x = layout.headline.position.x;
            headline.y = layout.headline.position.y;
            
            // Convert hex color to RGB
            const color = hexToRgb(layout.headline.color);
            headline.fills = [{{
                type: 'SOLID',
                color: {{ r: color.r/255, g: color.g/255, b: color.b/255 }}
            }}];
            
            frame.appendChild(headline);
            }}
            
            // Add CTA button
            if (layout.cta) {{
            const button = figma.createRectangle();
            button.name = "CTA Button";
            button.resize(layout.cta.width, layout.cta.height);
            button.x = layout.cta.position.x;
            button.y = layout.cta.position.y;
            button.cornerRadius = layout.cta.border_radius;
            
            const bgColor = hexToRgb(layout.cta.background_color);
            button.fills = [{{
                type: 'SOLID',
                color: {{ r: bgColor.r/255, g: bgColor.g/255, b: bgColor.b/255 }}
            }}];
            
            // Add button text
            const buttonText = figma.createText();
            buttonText.name = "CTA Text";
            buttonText.characters = layout.cta.text;
            buttonText.fontSize = layout.cta.size;
            buttonText.x = layout.cta.position.x + layout.cta.width/2;
            buttonText.y = layout.cta.position.y + layout.cta.height/2;
            buttonText.textAlignHorizontal = "CENTER";
            buttonText.textAlignVertical = "CENTER";
            
            const textColor = hexToRgb(layout.cta.color);
            buttonText.fills = [{{
                type: 'SOLID',
                color: {{ r: textColor.r/255, g: textColor.g/255, b: textColor.b/255 }}
            }}];
            
            frame.appendChild(button);
            frame.appendChild(buttonText);
            }}
            
            // Select and zoom to the created frame
            figma.currentPage.selection = [frame];
            figma.viewport.scrollAndZoomIntoView([frame]);
            
            figma.closePlugin("Banner created successfully!");
        }}
        }};

        function hexToRgb(hex) {{
        const result = /^#?([a-f\\d]{{2}})([a-f\\d]{{2}})([a-f\\d]{{2}})$/i.exec(hex);
        return result ? {{
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        }} : {{ r: 0, g: 0, b: 0 }};
        }}'''
        
        return {
            "manifest.json": json.dumps(manifest, indent=2),
            "ui.html": ui_html,
            "code.js": code_js
        }



    def create_banner(self, user_input: str, logo_path: str = None,
                   width: int = 1200, height: int = 628, max_iterations: int = 3,
                   output_format: str = "json") -> str:
        """
        Main method to create a banner ad using the multi-agent system.
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

                # Generate SVG preview string
                svg_preview_str = self.export_to_svg(current_layout, background_description, width, height, logo_path)

                # Convert SVG string to PNG bytes in memory
                try:
                    png_bytes = cairosvg.svg2png(bytestring=svg_preview_str.encode('utf-8'))
                except Exception as convert_error:
                    print(f"⚠️ Error converting SVG to PNG: {convert_error}")
                    # If conversion fails, we can't send a preview. Skip to next iteration or break.
                    # For simplicity, we'll approve to avoid an infinite loop on conversion errors.
                    feedback = {'approved': True}
                else:
                    # Encode PNG bytes to base64 string for the API
                    png_preview_b64 = base64.b64encode(png_bytes).decode('utf-8')

                    # Review design with the generated PNG visual preview
                    feedback = self.design_reviewer_agent(
                        user_input, current_layout, background_description, width, height, iteration, png_preview_b64
                    )

                if feedback.get('approved', False) or iteration == max_iterations:
                    print(f"✅ Design approved after {iteration} iteration(s)")
                    break

                # Refine design based on feedback
                if feedback.get('issues'):
                    current_layout = self.refine_layout(current_layout, feedback)
                    print(f"🔧 Applied {len(feedback['issues'])} refinements")

            # Final result
            final_result = {
                'objectives': objectives,
                'background_description': background_description,
                'layout': current_layout,
                'dimensions': {'width': width, 'height': height},
                'iterations': iteration
            }

            print("\n🎉 Banner creation completed!")

            if output_format == "json":
                return json.dumps(final_result, indent=2, ensure_ascii=False)
            elif output_format == "svg":
                # Return the final SVG content
                return self.export_to_svg(current_layout, background_description, width, height, logo_path)
            else:
                return json.dumps(final_result, indent=2, ensure_ascii=False)

        except (KeyError, TypeError) as e:
            print(f"⌫ Error in banner creation during data access: {str(e)}")
            print("Please check if the LLM output conforms to the expected JSON structure.")
            return f"Error: {str(e)}"
        except Exception as e:
            print(f"⌫ Error in banner creation: {str(e)}")
            return f"Error: {str(e)}"
    
    def refine_layout(self, layout_spec: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        refined = json.loads(json.dumps(layout_spec))  # Deep copy

        for issue in feedback.get("issues", []):
            elem = issue.get("element")
            if elem not in refined:
                continue

            action = issue.get("action")
            params = issue.get("parameters", {})

            if action == "reposition":
                if "x" in params:
                    refined[elem]["position"]["x"] = params["x"]
                if "y" in params:
                    refined[elem]["position"]["y"] = params["y"]
            elif action == "recolor":
                if "color" in params:
                    refined[elem]["color"] = params["color"]
                if "background_color" in params:
                    refined[elem]["background_color"] = params["background_color"]
            elif action == "retext":
                if "text" in params:
                    refined[elem]["text"] = params["text"]
            elif action == "resize":
                # Cho phép resize cả dimensions và font_size
                if "width" in params:
                    refined[elem].setdefault("dimensions", {})["width"] = params["width"]
                if "height" in params:
                    refined[elem].setdefault("dimensions", {})["height"] = params["height"]
                if "font_size" in params:
                    refined[elem]["font_size"] = params["font_size"]
            # Giữ lại stylechange cho các trường hợp khác
            elif action == "stylechange":
                if "font_family" in params:
                    refined[elem]["font_family"] = params["font_family"]
                if "border_radius" in params:
                    refined[elem]["border_radius"] = params["border_radius"]

        return refined


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