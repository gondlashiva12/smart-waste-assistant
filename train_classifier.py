"""
Train a waste image classifier and export it to ONNX.

This is the same script for both models - point it at a different
dataset/output name for the item classifier vs the bin classifier.

Expected dataset layout (standard torchvision ImageFolder format):

    dataset/
        plastic/
            img1.jpg
            img2.jpg
        paper/
            ...
        organic/
            ...
        e-waste/
            ...
        hazardous/
            ...

For the item classifier: use a dataset like TrashNet (plastic, paper,
metal/e-waste, glass, cardboard, trash), remapped to this project's
five categories.

For the bin classifier: use a dataset you collect yourself (photos of
clean / moderately full / overflowing bins), since no public dataset
matches this exact task - a few dozen photos per class, plus
augmentation, is a reasonable starting point for a hackathon timeline.

Usage:
    python train_classifier.py --data ./dataset/items --out item_classifier
    python train_classifier.py --data ./dataset/bins  --out bin_classifier

Produces models/<out>.onnx and models/<out.replace('_classifier','')>_labels.txt
"""

import argparse
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def train(data_dir: str, out_name: str, epochs: int, batch_size: int, lr: float):
    os.makedirs(MODELS_DIR, exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = datasets.ImageFolder(data_dir, transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    class_names = dataset.classes
    print(f"Classes found: {class_names}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # MobileNetV2 - small enough to run comfortably on-device, and a
    # reasonable starting point for NPU deployment via Qualcomm AI Hub.
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)

        print(f"Epoch {epoch + 1}/{epochs} - loss: {running_loss / total:.4f} - acc: {correct / total:.3f}")

    # Export to ONNX for use with onnxruntime (CPU now, QNN execution
    # provider later once you're on the Snapdragon device - see README.md).
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    onnx_path = os.path.join(MODELS_DIR, f"{out_name}.onnx")

    torch.onnx.export(
        model, dummy_input, onnx_path,
        input_names=["input"], output_names=["output"],
        dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
        opset_version=13,
    )
    print(f"Saved model to {onnx_path}")

    labels_path = os.path.join(MODELS_DIR, f"{out_name.replace('_classifier', '')}_labels.txt")
    with open(labels_path, "w", encoding="utf-8") as f:
        f.write("\n".join(class_names))
    print(f"Saved labels to {labels_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to ImageFolder-structured dataset")
    parser.add_argument("--out", required=True, help="Output name, e.g. item_classifier or bin_classifier")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    train(args.data, args.out, args.epochs, args.batch_size, args.lr)
