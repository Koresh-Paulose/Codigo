# Study Notes: The Transformer Architecture & Self-Attention

## 1. Overview
The Transformer is a deep learning architecture introduced in the 2017 paper "Attention Is All You Need" by Vaswani et al. It replaced recurrent neural networks (RNNs) and LSTMs for sequence-to-sequence tasks because it processes entire sequences in parallel instead of one token at a time.

## 2. Core Concepts
- **Self-Attention Mechanism**: Allows the model to weigh the importance of different tokens in an input sequence relative to one another, regardless of their distance.
- **Query, Key, and Value (Q, K, V)**: 
  - Each input token is projected into three vectors: Query ($Q$), Key ($K$), and Value ($V$).
  - Attention weights are computed by taking the dot product of $Q$ and $K^T$, dividing by $\sqrt{d_k}$ (scaling factor to prevent vanishing gradients), and applying softmax.
  - The resulting probability distribution multiplies $V$ to compute the attention output:
    $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
- **Multi-Head Attention**: Multiple independent attention heads project queries, keys, and values into different subspaces. This allows the model to simultaneously attend to information from different representation subspaces (e.g. syntactic agreement in one head, semantic context in another).
- **Positional Encoding**: Because Transformers have no inherent recurrence or convolutions, positional encodings (sinusoidal or learned vectors) are added to token embeddings so the model knows token order.
- **Feed-Forward Networks (FFN)**: Each attention layer is followed by a position-wise fully connected feed-forward network with non-linear activation (e.g. GELU or ReLU).
- **Residual Connections and Layer Normalization**: Add & Norm layers stabilize deep gradient flow and enable training models with hundreds of layers.

## 3. Why It Matters
- **Parallelization**: Eliminates sequential dependency of RNNs, enabling massive training on modern GPUs.
- **Long-Range Dependencies**: Directly connects any two tokens in $O(1)$ operations, eliminating the vanishing gradient problem over long sequences.
