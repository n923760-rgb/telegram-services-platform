def inputs(language="en"):
    names = (
        ("شركة الربيع للخدمات", "شركة الربيع للخدماث")
        if language == "ar"
        else ("Southern Office Services", "Southern Office Service")
    )
    return {
        "language": language,
        "delimiter": "comma",
        "whitespace": "preserve",
        "similarity": "conservative",
        "text": (
            "ID,Name,Note\n"
            f"00123,{names[0]},=1+1\n"
            f"00123,{names[1]},=1+1\n"
            f"00124,{names[1]},=1+1\n"
            f"00123,{names[0]},=1+1\n"
            "00123,,=1+1"
        ),
    }
