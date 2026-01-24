import asyncio
import edge_tts

text = """In a quiet village at the edge of the world, where the sky seemed close enough to touch, two friends shared a secret that no one else knew.

Luna had silver hair that shimmered like moonlight, and she carried a small lantern wherever she went. She had always felt drawn to the stars, watching them from her window each night, wondering where they went when they fell.

Kai was her best friend, a boy with messy dark hair and a tiny orange fox who rode on his shoulder. He was always ready to follow wherever curiosity led, and tonight, curiosity was calling.

A single star streaked across the twilight sky and disappeared beyond the forest. Luna grabbed her lantern. Kai whistled for his fox. They met at the village gate without a word, both knowing exactly where they needed to go.

The forest path was dark, but Luna's lantern lit the way. Fireflies danced around them as they walked deeper and deeper into the trees. And then, the path opened up, and they both gasped.

Below them lay Starfall Valley. Crystal trees glowed with soft blue and purple light. Stars drifted down from the sky like gentle snow, coming to rest among glowing flowers. A waterfall of pure starlight cascaded down distant cliffs, and streams of liquid light flowed through meadows of bioluminescent grass.

They descended carefully into the valley, reaching out to touch the crystal trees. The fox leaped from Kai's shoulder to chase a falling star, and Luna knelt beside one resting in the grass. It was warm, and it pulsed gently, like a tiny heartbeat.

Floating lily pads hovered above a starlight stream, and the children climbed aboard, riding them like boats through the magical landscape. The lily pads carried them to the heart of the valley, where an enormous ancient crystal tree stood, its roots spreading like rivers of light.

Tiny luminous creatures emerged from the flowers, moth-like beings with glowing wings. They landed on Luna's hands, trusting and gentle. The fox danced among them, creating swirling trails of light.

But as the children explored deeper, they found something troubling. Behind the starfall waterfall, a hidden cave held the valley's heart stone, a great crystal on a stone pedestal. It was cracked, and its light was fading. Without it, all the magic of the valley would slowly disappear.

Luna placed the fallen star she had found near the heart stone, and watched as blue light reached out from it, beginning to heal the cracks. Kai sent his fox to gather more fallen stars, and the luminous creatures joined in, carrying tiny stars in their wings.

Together, they all worked through the night. Star after star was brought to the heart stone, each one healing it a little more. Finally, Luna and Kai lifted one last great star together, and placed it on the pedestal.

A brilliant wave of light burst from the cave and swept across the entire valley. Crystal trees grew taller and brighter. New flowers bloomed in every color of starlight. The waterfall became twice as magnificent, and stars began falling in beautiful spirals instead of random drops.

The valley was reborn, more magical than ever before. The luminous creatures celebrated, forming living constellation patterns in the sky. They placed a crown of light on Luna's head, and gave Kai a crystal seed as thanks.

As the first light of dawn appeared on the horizon, the valley creatures gently guided the children back toward home. Luna hugged her new friends goodbye. Kai waved to the ancient tree. The fox looked back one last time.

They walked home through the sunrise forest, changed forever by what they had seen. Luna's lantern now glowed with permanent starlight, a piece of the valley she would always carry. Kai planted his crystal seed in the garden behind his house.

From their windows across the street, they waved to each other, smiling. And in Kai's garden, the crystal seed had already begun to sprout, one tiny glowing leaf reaching toward the fading stars.

The magic of Starfall Valley would always be with them. And perhaps, on quiet nights when the stars fall just right, they will return again.

Goodnight. May your dreams be full of falling stars."""


async def generate():
    communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural", rate="-15%")
    out_path = "output/audio/narration_full.mp3"
    await communicate.save(out_path)
    import os
    size = os.path.getsize(out_path)
    print(f"Narration saved: {out_path} ({size // 1024}KB)")


asyncio.run(generate())
