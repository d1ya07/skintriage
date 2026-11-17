"""FAQ knowledge base. The LLM may only answer from these facts.
The keyword lists power the offline fallback matcher."""

FAQS: list[dict] = [
    {
        "q": "What is SkinTriage?",
        "keywords": ["what is skintriage", "about", "what does this app", "purpose", "what can you do"],
        "a": "SkinTriage is a clinical decision-support and triage platform. You upload a photo of a "
             "skin concern, an AI model suggests a likely condition with a confidence score, a rule "
             "engine assigns an urgency level (low, moderate or high) and a matching specialist type, "
             "and you can then book an appointment. It is not a diagnostic tool.",
    },
    {
        "q": "Is the result a diagnosis?",
        "keywords": ["diagnosis", "accurate", "reliable", "trust the result", "replace doctor"],
        "a": "No. SkinTriage gives decision support only, not a diagnosis. Only a qualified medical "
             "professional can diagnose a skin condition, so always follow up with a doctor.",
    },
    {
        "q": "How does the skin scan work?",
        "keywords": ["skin scan", "scan work", "upload", "photo", "how does triage", "triage work", "analyse", "analyze"],
        "a": "From your patient dashboard open Skin Scan and upload a clear photo (JPG or PNG) of the "
             "skin concern. The model returns a likely condition, a confidence score, an urgency level "
             "and the recommended specialist type. From the result you can book that specialist directly. "
             "The model was trained on close-up dermatoscopic images, so ordinary phone photos may give "
             "less reliable results.",
    },
    {
        "q": "What do the urgency levels mean?",
        "keywords": ["urgency", "low", "moderate", "high", "levels", "tier"],
        "a": "Low means a routine appointment is suggested. Moderate means you should book a specialist "
             "soon. High means the result is flagged for urgent referral: you will see an urgent referral "
             "banner and should see a specialist as soon as possible.",
    },
    {
        "q": "What does the confidence score mean?",
        "keywords": ["confidence", "percentage", "score", "probability", "how sure"],
        "a": "The confidence score shows how sure the model is about its suggestion, from 0 to 100%. "
             "A low score means the suggestion should be treated with extra caution. Either way, the "
             "result is not a diagnosis.",
    },
    {
        "q": "How do I book an appointment?",
        "keywords": ["book", "booking", "book an appointment", "make an appointment", "appointment", "schedule", "slot"],
        "a": "Go to Find a doctor, filter by specialty or city, and click Book appointment. Pick a date "
             "and a 30-minute slot (Monday to Saturday, 9 AM to 5 PM IST), add the reason for your visit "
             "and confirm. The booking then appears under My appointments.",
    },
    {
        "q": "How do I cancel an appointment?",
        "keywords": ["cancel", "cancellation", "cancel an appointment", "cancel a booking", "cancel my", "delete appointment", "remove appointment"],
        "a": "Open My appointments, find the booking under Upcoming, click Cancel and confirm. The slot is "
             "released for other patients. Past appointments can't be cancelled.",
    },
    {
        "q": "Can I reschedule?",
        "keywords": ["reschedule", "change the time", "change the date", "change time", "change date", "move appointment", "move my"],
        "a": "There is no reschedule button yet. Cancel the existing appointment in My appointments, then "
             "book a new slot from Find a doctor.",
    },
    {
        "q": "Which specialists are available?",
        "keywords": ["specialist", "doctor types", "dermatologist", "oncologist", "surgeon", "physician", "which doctor"],
        "a": "The directory lists Dermatologists, Dermato-oncologists, Dermatologic Surgeons and General "
             "Physicians across partner hospitals. After a skin scan, SkinTriage suggests which type fits "
             "your result.",
    },
    {
        "q": "What can the skin scan assess?",
        "keywords": ["acne", "pimple", "rash", "bite", "burn", "what can it check", "what can the scan", "can it detect", "eczema", "wart"],
        "a": "The skin scan only assesses moles and pigmented skin spots: the 7 lesion types in the HAM10000 "
             "dataset it was trained on. It cannot assess acne, rashes, insect bites, burns, cuts, warts or "
             "infections, and results for those will be unreliable. If a result says Uncertain, or you are "
             "worried about any skin problem, book a doctor.",
    },
    {
        "q": "Tips for a good photo",
        "keywords": ["tips", "good photo", "picture quality", "blurry", "lighting", "how to take"],
        "a": "Use good natural light, keep the camera steady and in focus, fill the frame with the area of "
             "concern, photograph one spot at a time and don't use filters.",
    },
    {
        "q": "Is my data private?",
        "keywords": ["privacy", "private", "data", "secure", "security", "who can see", "stored"],
        "a": "Your photos, results and appointments are linked to your account and are only available "
             "after you log in. Passwords are stored hashed, never in plain text.",
    },
    {
        "q": "How do I create an account?",
        "keywords": ["sign up", "signup", "register", "create account", "new account"],
        "a": "Click Sign up, enter your name, email and a password of at least 8 characters, and "
             "optionally your skin type. Doctor and admin accounts are created by an administrator.",
    },
    {
        "q": "I forgot my password",
        "keywords": ["forgot", "reset password", "change password", "locked out", "can't log in", "cannot log in"],
        "a": "Password reset isn't available in this version yet. Please contact the platform "
             "administrator to regain access.",
    },
]


def facts_text() -> str:
    return "\n".join(f"- Q: {f['q']}\n  A: {f['a']}" for f in FAQS)


DEFAULT_ANSWER = (
    "I can help with questions about using SkinTriage: the skin scan, what urgency levels mean, "
    "booking or cancelling appointments, finding specialists, and your account. What would you like to know?"
)
