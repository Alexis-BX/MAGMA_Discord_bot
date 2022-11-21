from magma import Magma as magma_model
from magma.image_input import ImageInput

class Magma:
    def __init__(self):
        self.model = magma_model.from_checkpoint(
            config_path = "configs/MAGMA_v1.yml",
            checkpoint_path = "configs/mp_rank_00_model_states.pt",
            device = 'cuda:0'
        )

    def run(self, img_url, img_prompt):
        inputs =[
            ImageInput(img_url),
            img_prompt
        ]

        ## returns a tensor of shape: (1, 149, 4096)
        embeddings = self.model.preprocess_inputs(inputs)

        ## returns a list of length embeddings.shape[0] (batch size)
        output = self.model.generate(
            embeddings = embeddings,
            max_steps = 30,
            temperature = 0.7,
            top_k = 0,
        )

        return output
