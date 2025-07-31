import replicate
import dotenv
import os

dotenv.load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

output = replicate.run(
    "arnab-optimatik/vybe-virtual-tryon:b0ccd961710dd8c0980526aecefc7815449d1b1bfdae29c60a38760261b81d9e",
    input={
        "seed": 42,
        "prompt": "The pair of images highlights a same clothing on two models, no bags or arm accessories, high resolution, 4K, 8K; [IMAGE1] Cloth is worn by a model in a lifestyle setting.[IMAGE2] The same cloth is worn by another model in a lifestyle setting.",
        "size_width": 672,
        "make_square": True,
        "size_height": 896,
        "whiten_mask": False,
        "expand_ratio": 0.025,
        "output_format": "png",
        "guidance_scale": 30,
        "output_quality": 90,
        "num_inference_steps": 30,
        "model_image": "https://replicate.delivery/pbxt/NS0GpC5mn2BvNfSw1KmBdNE2juEof20xOxPXm8o9QV46uQvn/BradPitt-gty-sn-250612_1749763171607_hpMain.jpeg",
        "garment_image": "https://replicate.delivery/pbxt/NS0GpP8mJqXflzhIO1QgiQYNLNzdxpUC1Uv5bz4xMDwAMXFk/89e046e4-2239-45fe-9fdb-20ebbb3020fb.jpg",
    }
)

# The arnab-optimatik/vybe-virtual-tryon model can stream output as it's running.
# The predict method returns an iterator, and you can iterate over that output.
for item in output:
    # https://replicate.com/arnab-optimatik/vybe-virtual-tryon/api#output-schema
    print(item)