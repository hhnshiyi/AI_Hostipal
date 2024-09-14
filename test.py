import gradio as gr

# 假设我们有两个下拉框，一个用于选择学院，一个用于选择学院下的系
colleges = ["College of Arts", "College of Science"]
departments_A = ["Department of English", "Department of History"]
departments_B = ["Department of Physics", "Department of Chemistry"]

# 定义一个函数，根据选择的学院更新系的选项
def update_departments(college):
    if college == "College of Arts":
        return departments_A
    else:
        return departments_B

# 创建 Gradio 界面
with gr.Blocks() as demo:
    with gr.Row():
        college_dropdown = gr.Dropdown(choices=colleges, label="Select College",allow_custom_value=True)
        department_dropdown = gr.Dropdown(label="Select Department",allow_custom_value=True)
    # 当学院下拉框的值改变时，更新系下拉框的选项
    college_dropdown.change(update_departments, inputs=college_dropdown, outputs=department_dropdown)

demo.launch()