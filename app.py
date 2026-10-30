import streamlit as st
import json
import re

# محاولة استيراد مكتبة قراءة ملفات الـ PDF
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    try:
        import PyPDF2 as pypdf
        PDF_SUPPORT = True
    except ImportError:
        PDF_SUPPORT = False

# استيراد مكتبة الذكاء الاصطناعي Gemini
try:
    import google.generativeai as genai
    GEMINI_SUPPORT = True
except ImportError:
    GEMINI_SUPPORT = False

# إعدادات الصفحة
st.set_page_config(
    page_title="منصة امتحانات الثانوية العامة الذكية",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة بـ CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.3rem;
        color: #1E3A8A;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 25px;
    }
    .card {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .footer {
        text-align: center;
        color: #6B7280;
        margin-top: 50px;
        font-size: 0.95rem;
        border-top: 1px solid #e5e7eb;
        padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# إدارة حالة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- صفحة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div class='main-header'>🔐 بوابة الدخول لمنصة امتحانات الثانوية العامة</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>أدخل اسمك الثلاثي وكلمة المرور للمتابعة</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("login_form"):
            input_name = st.text_input("اسم الطالب الثلاثي", placeholder="اكتب اسمك هنا...")
            password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور...")
            submit_login = st.form_submit_button("دخول المنصة 🚀")
            
            if submit_login:
                if password == "01224982634" and input_name.strip() != "":
                    st.session_state.logged_in = True
                    st.session_state.username = input_name.strip()
                    st.success(f"✨ أهلاً بك يا {st.session_state.username}! جاري تحويلك...")
                    if hasattr(st, 'rerun'):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                elif password != "01224982634":
                    st.error("❌ كلمة المرور غير صحيحة.")
                else:
                    st.warning("⚠️ يرجى كتابة اسمك الثلاثي أولاً.")
        st.markdown("</div>", unsafe_allow_html=True)
                    
    st.markdown("<div class='footer'>تم تصميم وتطوير المنصة بواسطة المطور: <b>محمد عبد الله</b> 💻</div>", unsafe_allow_html=True)

else:
    # --- التطبيق الرئيسي ---
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=110)
        st.title(f"البطل: {st.session_state.username} 👋")
        st.markdown("---")
        
        st.header("⚙️ إعدادات الذكاء الاصطناعي")
        api_key = st.text_input("مفتاح Gemini API Key:", type="password", help="أدخل مفتاح Google Gemini API لتوليد الأسئلة المخصصة للملف")
        num_questions = st.number_input("عدد الأسئلة المطلوبة:", min_value=3, max_value=50, value=10, step=1)
        
        # خيار لتفعيل أو إلغاء تفعيل الاختبارات الثلاثة
        generate_three_levels = st.checkbox("إنشاء 3 اختبارات (سهل، متوسط، صعب)", value=True, help="إذا تم إلغاؤها، سيتم إنشاء اختبار واحد قياسي حسب العدد المحدد.")
        
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()
            
        st.markdown("<div style='text-align: center; color: #4b5563; margin-top: 20px;'><b>منصة الامتحانات الذكية</b><br>تطوير: <b>محمد عبد الله</b> 💻</div>", unsafe_allow_html=True)

    header_text = "📄 توليد 3 اختبارات (سهل، متوسط، صعب) من ملف PDF" if generate_three_levels else "📄 توليد اختبار ذكي مخصص من ملف PDF"
    st.markdown(f"<div class='main-header'>{header_text}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>قم برفع أي ملف PDF، وسيقوم النظام بتحليله بالذكاء الاصطناعي وإنشاء بنك أسئلة يعتمد 100% على محتوى ملف المادة المرفوع</div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("قم برفع ملف الـ PDF هنا:", type=["pdf"])
    
    # دالة ذكية لتوليد الأسئلة لمستوى معين أو امتحان واحد
    def generate_quiz_from_pdf_bytes(pdf_bytes, count, level, key):
        genai.configure(api_key=key)
        
        selected_model_name = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'gemini' in m.name:
                        selected_model_name = m.name
                        break
        except Exception:
            pass
            
        fallback_models = ['gemini-1.5-flash-latest', 'gemini-1.5-pro-latest', 'gemini-pro', 'gemini-1.5-flash']
        
        model = None
        if selected_model_name:
            try:
                model = genai.GenerativeModel(selected_model_name)
            except Exception:
                pass
                
        if not model:
            for f_model in fallback_models:
                try:
                    model = genai.GenerativeModel(f_model)
                    break
                except Exception:
                    continue
                    
        if not model:
            raise Exception("لم يتم العثور على أي نموذج مدعوم لتوليد المحتوى باستخدام مفتاح API هذا. يرجى التأكد من صحة المفتاح.")

        pdf_file_part = {
            "mime_type": "application/pdf",
            "data": pdf_bytes
        }

        if level:
            level_desc = {
                "سهل": "مستوى سهل ومباشر لقياس الفهم الأساسي واستخراج المعلومات الصريحة",
                "متوسط": "مستوى متوسط يتطلب فهماً وتحليلاً لبعض الأفكار الواردة",
                "صعب": "مستوى صعب ومعقد جداً يتطلب استنتاجاً وعمقاً وتفكيرًا نقدياً عالياً"
            }
            level_prompt_text = f"لمستوى ({level}) بحيث يكون: {level_desc[level]}"
        else:
            level_prompt_text = "بمستوى متقدم وشامل يغطي تفاصيل الملف بدقة"

        prompt = f"""
        أنت خبير محترف وممتحن معتمد لوضع امتحانات الثانوية العامة المصرية.
        مهمتك هي قراءة ملف الـ PDF المرفق بدقة متناهية، وتحديد تخصص المادة الموجودة فيه.
        أنشئ {count} أسئلة اختيارات من متعدد (MCQ) {level_prompt_text}.
        
        شروط صارمة وقاطعة:
        1. **الالتزام الحصري بالمادة:** ممنوع خلط المواد، والأسئلة يجب أن تطابق المحتوى بدقة.
        2. **التطابق الدقيق من محتوى الملف:** استخرج الأسئلة حصرياً من المستند المرفق.
        3. **توفير تلميح (Hint):** أضف تلميحاً ذكياً ومفيداً لكل سؤال يساعد الطالب على التفكير دون إعطاء الإجابة المباشرة.
        4. **الشرح التفصيلي:** قدم تفسيراً دقيقاً لكل إجابة صحيحة من واقع محتوى الملف المرفق.
        5. **التنسيق:** أرجع النتيجة في صيغة JSON حصة (Array of Objects) فقط بدون أي نصوص خارجية، بالتنسيق التالي:

        [
          {{
            "q": "نص السؤال الدقيق المرتبط بمحتوى الملف",
            "options": ["أ) الاختيار الأول", "ب) الاختيار الثاني", "ج) الاختيار الثالث", "د) الاختيار الرابع"],
            "answer": "أ) الاختيار الأول",
            "hint": "تلميح ذكي ومساعد لحل السؤال",
            "explanation": "شرح وتحليل تفصيلي لسبب صحة الإجابة ارتباطاً بجزئيات الملف المرفق"
          }}
        ]
        """
        
        response = model.generate_content([pdf_file_part, prompt])
        raw_text = response.text.strip()
        
        match = re.search(r'\[\s*\{.*\}\s*\]', raw_text, re.DOTALL)
        if match:
            clean_json_str = match.group(0)
        else:
            clean_json_str = raw_text.replace("```json", "").replace("```", "").strip()
            
        return json.loads(clean_json_str)

    if uploaded_file is not None:
        if not PDF_SUPPORT:
            st.error("مكتبة قراءة الـ PDF غير مثبتة. يرجى تثبيتها عبر التيرمينال باستخدام الأمر: `pip install pypdf`")
        elif not GEMINI_SUPPORT:
            st.error("مكتبة الذكاء الاصطناعي غير مثبتة. يرجى تثبيتها بالأمر: `pip install google-generativeai`")
        elif not api_key:
            st.warning("⚠️ يرجى أدخال مفتاح Google Gemini API Key في القائمة الجانبية لبدء التوليد.")
        else:
            btn_text = "🚀 تحليل الملف وتوليد الاختبارات الثلاثة" if generate_three_levels else "🚀 تحليل الملف وتوليد الاختبار الذكي"
            if st.button(btn_text):
                try:
                    with st.spinner("جاري قراءة وتحليل ملف المادة بالذكاء الاصطناعي..."):
                        bytes_data = uploaded_file.getvalue()
                        
                        if generate_three_levels:
                            st.session_state.quizzes = {
                                "سهل": generate_quiz_from_pdf_bytes(bytes_data, num_questions, "سهل", api_key),
                                "متوسط": generate_quiz_from_pdf_bytes(bytes_data, num_questions, "متوسط", api_key),
                                "صعب": generate_quiz_from_pdf_bytes(bytes_data, num_questions, "صعب", api_key)
                            }
                        else:
                            st.session_state.quizzes = {
                                "الرئيسي": generate_quiz_from_pdf_bytes(bytes_data, num_questions, None, api_key)
                            }
                            
                        st.session_state.submitted_quiz = False
                        st.session_state.show_review_warning = False
                        st.success("✅ تم توليد بنك الأسئلة بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء تحليل الملف أو التوليد: {e}")

    # عرض المستويات والاختبارات إذا تم توليدها
    if "quizzes" in st.session_state and st.session_state.quizzes:
        st.markdown("---")
        
        if generate_three_levels:
            level_tabs = st.tabs(["🟢 المستوى السهل", "🟡 المستوى المتوسط", "🔴 المستوى الصعب"])
            levels = ["سهل", "متوسط", "صعب"]
        else:
            level_tabs = [st.container()]
            levels = ["الرئيسي"]

        placeholder_option = "-- اختر الإجابة --"

        for idx, tab in enumerate(level_tabs):
            current_level = levels[idx]
            with tab:
                quiz = st.session_state.quizzes[current_level]
                st.info(f"اختبار **{current_level}** مكون من **{len(quiz)} سؤالاً**.")
                
                with st.form(f"exam_form_{current_level}"):
                    user_answers = {}
                    for i, q_data in enumerate(quiz):
                        st.markdown(f"**السؤال {i+1}: {q_data['q']}**")
                        
                        if q_data.get('hint'):
                            st.caption(f"💡 **تلميح:** {q_data['hint']}")
                            
                        options_with_placeholder = [placeholder_option] + q_data['options']
                        selected_val = st.radio(
                            f"اختر الإجابة للسؤال {i+1}:", 
                            options_with_placeholder,
                            index=0,
                            key=f"q_{current_level}_{i}"
                        )
                        
                        user_answers[i] = None if selected_val == placeholder_option else selected_val
                        st.markdown("---")
                    
                    submit_clicked = st.form_submit_button(f"📩 إرسال وتصحيح الاختبار")

                if submit_clicked:
                    st.session_state.current_active_level = current_level
                    st.session_state.temp_user_answers = user_answers
                    st.session_state.show_review_warning = True

        # عرض رسالة التحذير والتأكيد عند الضغط على إرسال
        if st.session_state.get("show_review_warning", False):
            active_lvl = st.session_state.current_active_level
            st.warning("⚠️ عارفين انك شاطر راجع الاجابات عشان تتأكد تماماً قبل التسليم النهائي!")
            
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                if st.button("🔍 مراجعة الاجابات"):
                    st.session_state.show_review_warning = False
                    if hasattr(st, 'rerun'):
                        st.rerun()
                    else:
                        st.experimental_rerun()
            with col_rev2:
                if st.button("✅ تسليم الاختبار على طول"):
                    st.session_state.submitted_quiz = True
                    st.session_state.submitted_level = active_lvl
                    st.session_state.user_answers = st.session_state.temp_user_answers
                    st.session_state.show_review_warning = False
                    if hasattr(st, 'rerun'):
                        st.rerun()
                    else:
                        st.experimental_rerun()

        # عرض النتيجة والشرح واقتراح الاختبار التالي
        if st.session_state.get("submitted_quiz", False):
            active_lvl = st.session_state.submitted_level
            quiz = st.session_state.quizzes[active_lvl]
            score = 0
            total = len(quiz)
            
            st.markdown(f"## 📊 النتيجة التفصيلية للاختبار:")
            
            for i, q_data in enumerate(quiz):
                correct_ans = q_data['answer']
                user_ans = st.session_state.user_answers.get(i)
                
                if user_ans == correct_ans:
                    score += 1
                    st.success(f"✔️ السؤال {i+1}: إجابة صحيحة وموفقة!")
                else:
                    st.error(f"❌ السؤال {i+1}: إجابة خاطئة!")
                    st.write(f"- **إجابتك:** {user_ans if user_ans else 'لم تُجب'}")
                    st.write(f"- **الإجابة النموذجية الصحيحة:** {correct_ans}")
                
                if "explanation" in q_data:
                    st.info(f"💡 **الشرح والتحليل التفاعلي:** {q_data['explanation']}")
                st.markdown("---")
            
            percentage = (score / total) * 100
            st.metric("النتيجة النهائية", f"{score} / {total}", f"{percentage:.1f}%")
            
            if percentage >= 85:
                st.balloons()
                st.success("🌟 مستوى ممتاز جداً وعقلية تحليلية واعدة!")
            elif percentage >= 50:
                st.warning("💪 أداء جيد، راجع الشرح لتثبيت معلوماتك.")
            else:
                st.error("📚 يحتاج هذا الاختبار لمزيد من التركيز والمراجعة.")

            # اقتراح الاختبار الآخر عند الانتهاء (في حال كانت الاختبارات الثلاثة مفعلة)
            if generate_three_levels:
                st.markdown("---")
                st.markdown("### 🎯 اقتراح لك:")
                if active_lvl == "سهل":
                    st.info("لقد انهيت الاختبار السهل بنجاح! ننصحك الآن بالانتقال إلى **المستوى المتوسط** لتحدي قدراتك.")
                elif active_lvl == "متوسط":
                    st.info("أداء رائع في المستوى المتوسط! هل أنت مستعد لخوض التحدي الأكبر في **المستوى الصعب**؟")
                elif active_lvl == "صعب":
                    st.success("لقد أنهيت الاختبار الصعب بنجاح تام! أنت جاهز تماماً للامتحان النهائي.")