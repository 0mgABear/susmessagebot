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
    ("We are looking for reliable partners for long-term collaboration!\nNo risks or shady deals!\nEarn between $1400 and 1600$ per week\nConsistent income—can also be done remotely!\n\nIf you're interested, contact @Anna_Lour", "BAN")
    ('i can send that message too and see if my bot bans me haha', "SAFE"),
    ("I am offering you a wide range of services like finding valid business emails and targeted b2b LinkedIn lead generation by sales navigator. I am excellent at providing clean, bounce-free, Geo-targeted leads based on your targeted market.\n\n\n\nI am an expert in:\n\n\n\nB2B Lead Generation\nLinkedin Lead Generation\nB2B targeted emails\nValid Emails\nData Collection and Research\nWeb research\nWeb Scrapping\nData Entry\nCoinbase leads\nSweepstakes leads\nGambler leads\nForex leads\nCrypto leads\nTrading leads\nB2c leads\nLead generation \n\n\nMy tools and resources:\n\nLinkedin sales navigator\nE-mail Finder & Verification Tools \nGoogle Advanced Search \nZoominfo, Yellow Page, Crunchbase, AngelList, Yelp\nCompany Website, and so on.\n\n\nHere's what I need from you:\n\nTargeted Industries\nTargeted Locations\nTargeted contact titles\nTargeted employee size(if needed)\n\n\nWhy you should appoint me.!\n\n\n\nFast response\n100% accuracy\nReplacement for invalid leads\n24/7 support\n\nDrop message \n@Creative_Lead_MWC\n@rpaexpert\nhttps://wa.me/+923710042488", "BAN"),
    ('Australia 🇦🇺 | Canada 🇨🇦 | UK | Denmark 🇩🇰 | 🇬🇧USA 🇺🇸 + Toll Free and Local Number is available\n\n𝗦𝗜𝗣 𝗧𝗿𝘂𝗻𝗸𝘀 & 𝗗𝗜𝗗𝘀 – 𝗥𝗲𝗮𝗱𝘆\n 𝗜𝗻𝘀𝘁𝗮𝗻𝘁 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗶𝗼𝗻 𝗼𝗻 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱 𝗥𝗼𝘂𝘁𝗲𝘀 \n\nUp to 20 channels \n🛎️ message me now to get yours\n@Cloudcallvoip', "BAN"),
    ('info. @ra_Cyt', "BAN"),
    ('Quickie @ra_Cyt', "BAN"),
    ('@slimsgGirl', "BAN"),
    ('She’s allowed? @ra_Cyt', "BAN"),
    ('noooo not my thing, if anyones giving away free openai credits, then send them my way :D /j', "SAFE"),
    ('yesss let it be reinforced :DD', "SAFE"),
    ('ikik', "SAFE"),
    ('issok', "SAFE"),
    ('It’s all credits', "SAFE"),
    ('oh WHAT', "SAFE"),
    ('as i was ssaying', "SAFE"),
    ('they say 99%', "SAFE"),
    ('Fr', "SAFE"),
    ('Sjksfngasf', "SAFE"),
    ('ah ykw', "SAFE"),
    ('FRRRR (this is gonna get banned ngl)', "SAFE"),
    ("iut's open sourcce gais", "SAFE"),
    ('Ah icic', "SAFE"),
    ('oh but 50 requests a day :<', "SAFE"),
    ('Chop chop chop wrk 5.9k pm free job fast job', "BAN"),
    ('Urgent wrk paynow 1.9k , check my story if you do pm', "BAN"),
    ('how is the human trafficking from sg to jb now', "SAFE"),
    ('Heyyy\n☺️☺️', "BAN"),
    ('woodlands any vep check?', "SAFE"),
    ('any new abt jb to sg? @Rac_yy', "BAN"),
    ('@qzvxlp', "BAN"),
    ('💯JOM 𝗩𝗖❤️\nVC BOGEL☑️\nVIDEO PRVCY☑️\nGROUP VIDEO☑️\n\n𝗡𝗔𝗞 𝗢𝗥𝗗𝗘𝗥 𝗠𝗘𝗦𝗘𝗝 𝗜 𝗕𝗕𝗬 @AnisaZahra69 💦', "BAN"),
    ('qwen 3.5 0.8b will be', "SAFE"),
]


if __name__ == "__main__":
    for message, label in examples:
        add_example(message, label)
        print(f"Added [{label}]: {message[:50]}...")
    print(f"\nDone! {len(examples)} examples added to ChromaDB.")
