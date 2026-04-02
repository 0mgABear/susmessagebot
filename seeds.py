from vector_store import add_example

examples = [
    ("🇺🇸 +1888 • 🇦🇺 +61 #WTS DID & SIP Trunk — Ready Now @Activepaidviop", "BAN"),
    ("Giving away my 15-inch MacBook Air (M4) — barely used and still in excellent condition. DM me.", "BAN"),
    ("📢 Students! Need Academic Help? Get expert help in Assignments, Homework, Online classes. Fast • Reliable • Affordable 👉 TutorSolve", "BAN"),
    ("Hi all! I lost my v!rg!n!ty at Valour House today... If anyone has seen it please let me know!", "BAN"),
    ("QX Automatic Mahjong Table – giving away brand new, comes complete with tiles. If interested DM me.", "BAN"),
    ("給她發Pm，以獲得很酷的服務，非常合法的弓工作和性愛", "BAN"),
    ("@Yrsgsuregirl", "BAN"),
    ("Hey guys I'm looking for a developer to join me on the VIP program comfortable in coding blockchain and AI ML. Deadline is in a few hours.", "SAFE"),
    ("Hi, im looking for a black wallet at either LT38, around icube or the bus stop. If found please pm me thank you.", "SAFE"),
    ("Check out this open source project: https://github.com/0mgABear/susmessagebot", "SAFE"),
    ("https://github.com/0mgABear/susmessagebot", "SAFE"),
    ("Looking for 1–3 people for remote earnings . Everything can be done from your phone. Income — €1,500 per week. Message 👉 @realewan", "BAN"),
    ('i can send it if u want?', "SAFE"),
]

if __name__ == "__main__":
    for message, label in examples:
        add_example(message, label)
        print(f"Added [{label}]: {message[:50]}...")
    print(f"\nDone! {len(examples)} examples added to ChromaDB.")