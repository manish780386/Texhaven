"""Text rules. weight = rough probability (0-100) that a message matching the rule is malicious."""
import re

I = re.IGNORECASE

# (code, category, weight, label, compiled regex)
RULES = [
    ("otp_request", "credential_theft", 45, "Asks you to share a one-time code, PIN or CVV",
     re.compile(r"\b(share|send|give|tell|forward|read out)\b.{0,30}\b(otp|one[- ]time (password|code)|verification code|security code|pin|cvv)\b", I)),
    ("credential_phish", "credential_theft", 25, "Asks you to verify or update account details",
     re.compile(r"\b(verify|confirm|update|validate|re-?activate)\b.{0,40}\b(account|bank|card|kyc|password|identity|details|payment|login)\b", I)),
    ("account_threat", "credential_theft", 25, "Warns that your account or card will be blocked",
     re.compile(r"\b(account|card|sim|wallet|number)\b.{0,40}\b(suspend(ed)?|block(ed)?|lock(ed)?|deactivat\w*|clos(ed|ure)|expire[sd]?|limited)\b", I)),
    ("urgency", "pressure", 15, "Creates artificial urgency",
     re.compile(r"\b(urgent(ly)?|immediately|within \d+ ?(hours?|hrs?|minutes?|mins?)|last warning|final notice|act now|today only|expires? (today|soon))\b", I)),
    ("prize", "prize_scam", 40, "Claims you won a prize or reward",
     re.compile(r"\b(you('ve| have)? (won|been selected)|congratulations.{0,30}(won|prize|reward|gift)|lottery|jackpot|claim (your )?(prize|reward|gift))\b", I)),
    ("fee_request", "payment_scam", 25, "Asks for a fee, tax or deposit",
     re.compile(r"\b(pay|send|transfer|deposit)\b.{0,30}\b(fees?|charges?|tax|customs|fine|deposit)\b", I)),
    ("untraceable_payment", "payment_scam", 25, "Mentions gift cards, crypto or wire transfers",
     re.compile(r"\b(gift ?cards?|itunes card|google play card|steam card|bitcoin|usdt|wire transfer|western union)\b", I)),
    ("courier", "delivery_scam", 25, "Fake delivery or customs problem",
     re.compile(r"\b(package|parcel|delivery|courier|shipment)\b.{0,50}\b(failed|held|pending|unable|address|fee|reschedul\w*|customs|redeliver\w*)\b", I)),
    ("tax_refund", "government_scam", 25, "Fake tax refund or penalty",
     re.compile(r"\b(tax|irs|hmrc|income tax)\b.{0,40}\b(refund|rebate|owed|pending|overdue|penalty)\b", I)),
    ("investment", "investment_scam", 35, "Promises guaranteed or risk-free returns",
     re.compile(r"\b(guaranteed|assured)\b.{0,30}\b(returns?|profit|income)\b|\b(double your|100% (profit|return)|risk[- ]free)\b|\b(forex|crypto|stock) (tips|signals?|group)\b", I)),
    ("job_offer", "job_scam", 30, "Too-good-to-be-true job offer",
     re.compile(r"\b(work from home|part[- ]time job|earn \$?\d+.{0,15}(per|a|/) ?(day|hour|week))\b", I)),
    ("family_impersonation", "impersonation", 40, "Pretends to be a family member on a new number",
     re.compile(r"\b(hi|hello) (mom|mum|dad)\b.{0,60}\b(new number|lost my phone|phone (broke|broken))\b", I)),
    ("sensitive_ask", "credential_theft", 35, "Asks for ID, card or bank details",
     re.compile(r"\b(send|share|reply with|provide|enter)\b.{0,30}\b(aadhaar|ssn|social security|passport|pan card|bank details|card number|routing number|iban)\b", I)),
    ("threat", "threat", 80, "Contains a threat of violence",
     re.compile(r"\b(i('ll| will| am going to)|gonna)\b.{0,20}\b(kill|hurt|find you|beat|destroy|stab|shoot|burn)\b|\byou('re| are) (dead|going to die)\b|\bwatch your back\b", I)),
    ("extortion", "threat", 70, "Looks like blackmail or extortion",
     re.compile(r"\b(pay (me|up)|i('ll| will) (leak|expose|post|release|share))\b.{0,40}\b(photos?|videos?|nudes?|pictures?|secrets?|messages?)\b|\bi (have|hacked|recorded) (your|you)\b", I)),
    ("harassment", "harassment", 70, "Contains abusive or harassing language",
     re.compile(r"\b(kill yourself|kys|go die|nobody (likes|wants) you|you('re| are) (worthless|disgusting|pathetic))\b", I)),
]

# Categories that are never acceptable to send, whatever the score.
HARD_BLOCK = {"threat", "harassment"}

ADVICE = {
    "credential_theft": "Never share OTPs, PINs or passwords. Banks never ask for them by SMS. Contact your bank using the number on your card.",
    "pressure": "Scammers rush you so you do not think. Pause and verify through an official channel.",
    "prize_scam": "You cannot win a contest you did not enter. Do not click links or pay any fee.",
    "payment_scam": "Be very careful with requests for fees, gift cards or crypto. Legitimate organisations do not ask for these by text.",
    "delivery_scam": "Check tracking directly on the courier's official website or app, not through the link in the text.",
    "government_scam": "Tax agencies do not send refund links by SMS. Visit the official government site by typing the address yourself.",
    "investment_scam": "Guaranteed returns do not exist. Be cautious of unsolicited trading tips.",
    "job_scam": "Real employers do not pay high daily wages for simple tasks or ask for money upfront.",
    "impersonation": "Call the person on their old number before sending money or information.",
    "threat": "This looks like a threat. Keep the message, do not reply, and consider reporting it to the police.",
    "harassment": "This looks like harassment. Block the sender and report it.",
    "link": "Do not tap unknown links. Type the website address yourself or use the official app.",
}
