import base64

from app.core.config import settings

def generate_summary_from_prompt(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
        reasoning={"effort": "low"},
    )

    return response.output_text

def describe_image(image_bytes: bytes, image_ext: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Mo ta ngan gon noi dung hinh anh nay bang tieng Viet, "
                            "tap trung vao thong tin huu ich cho viec tom tat tai lieu "
                            "(bieu do, so lieu, so do, y nghia hinh anh). "
                            "Neu la logo/anh trang tri khong mang thong tin, tra loi dung 1 cau ngan xac nhan dieu do."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/{image_ext};base64,{base64_image}",
                    },
                ],
            }
        ],
        reasoning={"effort": "low"},
    )

    return response.output_text

def transcribe_page_image(image_bytes: bytes) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Doc va chep lai toan bo noi dung trang tai lieu nay thanh van ban. "
                            "Giu nguyen cong thuc toan hoc duoi dang LaTeX neu co. "
                            "Giu bang bieu duoi dang markdown table. "
                            "Dung '## ' cho tieu de muc neu co. "
                            "Chi tra ve noi dung da chep lai, khong them binh luan hay giai thich gi them."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}",
                    },
                ],
            }
        ],
        reasoning={"effort": "low"},
    )

    return response.output_text
