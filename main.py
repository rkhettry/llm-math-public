import streamlit as st
import time
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv  # Import dotenv

from llm import MathSolver  # Import the MathSolver class

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")  # Get the API key from the environment

# Configure the Streamlit layout
st.set_page_config(layout="wide", page_title="Interactive Math Solver")

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_expression' not in st.session_state:
    st.session_state.current_expression = ""

if 'problem_state' not in st.session_state:
    st.session_state.problem_state = {
        'original_problem': None,
        'steps': None,
        'current_step': 0,
        'expected_answer': None,
        'variables': set(),
        'awaiting_answer': False,
        'final_answer': None
    }

# Initialize the MathSolver instance
if 'solver' not in st.session_state:
    st.session_state.solver = MathSolver(API_KEY)  # Use the API key from the environment

# Initialize session state
if 'input_buffer' not in st.session_state:
    st.session_state.input_buffer = ""

def create_calculator_sidebar():
    """Create the calculator sidebar with all buttons"""
    st.sidebar.header("Advanced Calculator")

    # Advanced operations
    st.sidebar.subheader("Advanced Operations")
    cols = st.sidebar.columns(4)
    advanced_ops = [
        ("d/dx", r"\frac{d}{dx}"),
        ("∫", r"\int"),
        ("∫_a^b", r"\int_{a}^{b}"),
        ("lim", r"\lim_{x \to }"),
        ("Σ", r"\sum_{i=1}^{n}")
    ]
    for i, (op, latex) in enumerate(advanced_ops):
        with cols[i % 4]:
            st.latex(latex)
            if st.button(op, key=f"adv_{op}", use_container_width=True):
                if op == "∫":
                    st.session_state.input_buffer += "∫() dx "  # Indefinite integral template
                elif op == "∫_a^b":
                    st.session_state.input_buffer += "∫_a^b () dx "  # Definite integral template
                elif op == "lim":
                    st.session_state.input_buffer += "lim_{x→} () "  # Limit template
                elif op == "Σ":
                    st.session_state.input_buffer += "Σ_{i=1}^n () "  # Summation template
                else:
                    st.session_state.input_buffer += f" {op} "

    # Functions
    st.sidebar.subheader("Functions")
    cols = st.sidebar.columns(3)
    functions = ["sin", "cos", "tan", "log", "exp"]
    for i, func in enumerate(functions):
        with cols[i % 3]:
            st.latex(func)
            if st.button(func, key=f"func_{func}", use_container_width=True):
                st.session_state.input_buffer += f"{func}("

    # Clear button
    if st.sidebar.button("Clear", key="clear_expr", use_container_width=True):
        st.session_state.input_buffer = ""

    # Add a spacer for better layout
    st.sidebar.markdown("---")

    # Keyboard shortcuts info
    with st.sidebar.expander("Keyboard Shortcuts"):
        st.markdown("""
        - `Enter`: Submit input
        - `Ctrl + Z`: Undo last step
        - `Ctrl + L`: Clear input
        - `Ctrl + H`: Show/hide hints
        """)

def main():
    # Add LaTeX support CSS
    st.markdown("""
        <style>
        .katex-html {
            display: none;
        }
        .correct-answer {
            background-color: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .incorrect-answer {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .validation-feedback {
            font-size: 0.9em;
            margin-top: 5px;
        }
        .step-instruction {
            font-weight: bold;
            color: #0066cc;
        }
        .calculator-button {
            margin: 2px;
            min-height: 40px;
        }
        
        /* Center the input form */
        .input-container {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 10px;
        }
        
        /* Style for the Ask Raze section */
        .stExpander {
            max-width: 300px;
        }

        /* Popup container */
        .popup-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }

        .popup-content {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            width: 400px;
            max-width: 90%;
            z-index: 1001;
        }

        .popup-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .popup-close {
            cursor: pointer;
            font-size: 24px;
            color: #666;
        }

        .popup-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .popup-button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            flex: 1;
        }

        .quick-hint {
            background-color: #ff4b4b;
            color: white;
        }

        .ask-question {
            background-color: #0066cc;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title in main area
    st.title("Interactive Math Solver")

    # Create calculator sidebar
    create_calculator_sidebar()

    # Main chat container
    chat_container = st.container()

    # Input area at the bottom with a form
    with st.container():
        with st.form(key='input_form', clear_on_submit=True):
            user_input = st.text_input("Your Input:", value=st.session_state.input_buffer)
            submit_button = st.form_submit_button(label='Submit')

    # Process the input when the form is submitted
    if submit_button and user_input:
        # Update session state
        st.session_state.input_buffer = ''  # Clear the input buffer after submission
        st.session_state.user_input = user_input  # Set the user input for processing

        # Process the input
        user_input = st.session_state.user_input

        # Check if we're awaiting the problem or an answer to a step
        if st.session_state.problem_state['steps'] is None:
            # User has input the original problem
            st.session_state.problem_state['original_problem'] = user_input

            # Process the problem using MathSolver
            with st.spinner("Processing the problem..."):
                try:
                    # Use the solver from session state
                    solution = st.session_state.solver.get_math_solution(user_input)
                    st.session_state.problem_state['steps'] = solution.steps
                    st.session_state.problem_state['final_answer'] = solution.final_answer
                    st.session_state.problem_state['current_step'] = 0
                    st.session_state.problem_state['awaiting_answer'] = True

                    # Add assistant's message introducing the problem
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Let's solve this problem step by step: {solution.original_problem}",
                        "timestamp": time.strftime("%H:%M"),
                        "requires_input": False
                    })

                    # Clear user input
                    st.session_state.user_input = ''
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing problem: {str(e)}")
        else:
            # User has input an answer to a step
            current_step = st.session_state.problem_state['current_step']
            steps = st.session_state.problem_state['steps']
            expected_answer = steps[current_step].answer

            # Use the validation function
            try:
                is_correct = st.session_state.solver.validate_step_answer_llm(user_input, expected_answer)

            except Exception as e:
                is_correct = False

            # Add user's answer to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": time.strftime("%H:%M")
            })

            if is_correct:
                # Correct answer
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"✅ Correct! {steps[current_step].explanation}",
                    "timestamp": time.strftime("%H:%M"),
                    "requires_input": False
                })
                # Move to next step
                st.session_state.problem_state['current_step'] += 1
                st.session_state.user_input = ''
                if st.session_state.problem_state['current_step'] >= len(steps):
                    # All steps completed
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Great job! The final answer is: {st.session_state.problem_state['final_answer']}",
                        "timestamp": time.strftime("%H:%M"),
                        "requires_input": False
                    })
                    # Reset problem state for a new problem
                    st.session_state.problem_state = {
                        'original_problem': None,
                        'steps': None,
                        'current_step': 0,
                        'expected_answer': None,
                        'variables': set(),
                        'awaiting_answer': False,
                        'final_answer': None
                    }
                else:
                    # Present next step
                    next_step = st.session_state.problem_state['steps'][st.session_state.problem_state['current_step']]
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"**Step {st.session_state.problem_state['current_step'] + 1}:** {next_step.instruction}\n\n{next_step.question}",
                        "timestamp": time.strftime("%H:%M"),
                        "requires_input": True
                    })
                st.rerun()
            else:
                # Incorrect answer
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"❌ That's not quite right. Try again!",
                    "timestamp": time.strftime("%H:%M"),
                    "requires_input": True
                })
                st.session_state.user_input = ''
                st.rerun()

    # If we have steps and awaiting user's answer
    if st.session_state.problem_state['steps'] is not None and st.session_state.problem_state['awaiting_answer']:
        # Present current step if not already presented
        if not any(msg.get('requires_input') for msg in st.session_state.chat_history if msg['role'] == 'assistant'):
            current_step = st.session_state.problem_state['current_step']
            next_step = st.session_state.problem_state['steps'][current_step]
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"**Step {current_step + 1}:** {next_step.instruction}\n\n{next_step.question}",
                "timestamp": time.strftime("%H:%M"),
                "requires_input": True
            })

    # Display chat history
    with chat_container:
        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"]):
                st.markdown(f"<div class='step-indicator'>{message['timestamp']}</div>",
                            unsafe_allow_html=True)

                if message["role"] == "user":
                    # Display user messages as regular text
                    st.write(message["content"])
                else:
                    content = message["content"]

                    # Handle the final answer message differently
                    if "The final answer is:" in content:
                        prefix = content.split("The final answer is:")[0]
                        final_answer = content.split("The final answer is:")[-1].strip()

                        # Display the prefix if it exists
                        if prefix.strip():
                            st.write(prefix.strip())

                        # Display "The final answer is:" and the LaTeX expression
                        st.write("The final answer is:")
                        # Remove any existing $ signs and display as LaTeX
                        final_answer = final_answer.strip().strip('$')
                        st.latex(final_answer)
                    else:
                        # Split the content into text and LaTeX parts
                        parts = content.split("$")

                        for i, part in enumerate(parts):
                            if i % 2 == 0:  # Regular text
                                if part.strip():  # Only display if not empty
                                    if part.startswith("Step"):
                                        st.markdown(f"**{part}**")
                                    else:
                                        st.write(part.strip())
                            else:  # LaTeX expression
                                if part.strip():  # Only display if not empty
                                    st.latex(part.strip())

                if message.get("requires_input"):
                    # Right-aligned Ask Raze expander
                    with st.container():
                        col1, col2 = st.columns([7, 3])
                        with col2:
                            with st.expander("Ask Raze 🤖"):
                                col1, col2 = st.columns([1, 1])
                                
                                # Get step number for both hint types
                                step_num = None
                                current_step = None
                                if "Step " in message["content"]:
                                    try:
                                        step_num = int(message["content"].split("Step ")[1].split(":")[0]) - 1
                                        current_step = st.session_state.problem_state['steps'][step_num]
                                    except (IndexError, ValueError, AttributeError):
                                        st.write("Error: Could not determine current step.")
                                        return

                                # Initialize session state for this step if needed
                                step_key = f"show_question_input_{step_num}"
                                if step_key not in st.session_state:
                                    st.session_state[step_key] = False

                                with col1:
                                    if st.button("Show Hint", key=f"hint_{idx}"):
                                        remaining_hints = max(0, 3 - current_step.hint_count)
                                        if remaining_hints > 0:
                                            hint = current_step.explanation
                                            current_step.hint_count += 1
                                            
                                            # Display hint with proper LaTeX formatting
                                            hint_parts = hint.split("$")
                                            for i, part in enumerate(hint_parts):
                                                if i % 2 == 0:  # Regular text
                                                    if part.strip():
                                                        st.write(part.strip())
                                                else:  # LaTeX expression
                                                    if part.strip():
                                                        st.latex(part.strip())
                                        else:
                                            st.warning("You've reached the maximum number of hints for this step.")

                                with col2:
                                    if st.button("Ask Custom Question", key=f"custom_{idx}"):
                                        st.session_state[step_key] = not st.session_state[step_key]

                                if st.session_state[step_key]:
                                    # Get previous attempts for this step
                                    previous_attempts = [
                                        msg["content"] 
                                        for msg in st.session_state.chat_history 
                                        if msg["role"] == "user" and 
                                        msg.get("step_num") == step_num
                                    ]

                                    user_question = st.text_input(
                                        "",  # Label hidden
                                        key=f"hint_input_{idx}",
                                        placeholder="Need clarification? Ask Raze..."
                                    )
                                    
                                    if st.button("Ask", key=f"ask_{idx}"):
                                        remaining_hints = max(0, 3 - current_step.hint_count)
                                        if remaining_hints > 0:
                                            hint = st.session_state.solver.generate_custom_hint(
                                                current_step,
                                                user_question,
                                                previous_attempts
                                            )
                                            current_step.hint_count += 1
                                            
                                            # Display hint with proper LaTeX formatting
                                            hint_parts = hint.split("$")
                                            for i, part in enumerate(hint_parts):
                                                if i % 2 == 0:  # Regular text
                                                    if part.strip():
                                                        st.write(part.strip())
                                                else:  # LaTeX expression
                                                    if part.strip():
                                                        st.latex(part.strip())
                                        else:
                                            st.warning("You've reached the maximum number of hints for this step.")

                                # Display hint count
                                if current_step:
                                    remaining_hints = max(0, 3 - current_step.hint_count)
                                    st.caption(f"Remaining hints: {remaining_hints}")

    # Reset states on submit
    if submit_button and user_input:
        st.rerun()

if __name__ == "__main__":
    main()
