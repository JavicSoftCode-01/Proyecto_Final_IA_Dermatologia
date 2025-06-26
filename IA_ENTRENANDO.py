import os
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.applications import MobileNetV2, ResNet50
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Concatenate, Input
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import Sequence
from tqdm import tqdm
from tqdm.keras import TqdmCallback


class BalancedDataGenerator(Sequence):
  def __init__(self, df, label_cols, image_dir, batch_size=32, target_size=(224, 224), augmentor=None,
               is_validation=False, samples_per_class=2000):
    super().__init__()
    self.df = df.copy().reset_index(drop=True)
    self.label_cols = label_cols
    self.image_dir = image_dir
    self.batch_size = batch_size
    self.target_size = target_size
    self.augmentor = augmentor
    self.is_validation = is_validation
    self.samples_per_class = samples_per_class
    if not self.is_validation:
      self.resample_indices()
    else:
      self.resampled_indices = self.df.index.tolist()

  def __len__(self):
    return int(np.floor(len(self.resampled_indices) / self.batch_size))

  def __getitem__(self, index):
    start_index = index * self.batch_size
    end_index = (index + 1) * self.batch_size
    batch_indices = self.resampled_indices[start_index:end_index]
    batch_df = self.df.iloc[batch_indices]
    X = np.empty((len(batch_df), *self.target_size, 3), dtype=np.float32)
    for i, row in enumerate(batch_df.itertuples()):
      img_path = os.path.join(self.image_dir, row.image_with_ext)
      try:
        img = cv2.imread(img_path)
        if img is not None:
          img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
          img = cv2.resize(img, self.target_size)
          if self.augmentor and not self.is_validation:
            img = self.augmentor.random_transform(img)
          X[i,] = img / 255.0
        else:
          X[i,] = np.zeros((*self.target_size, 3))
      except Exception as e:
        print(f"Error loading image {img_path}: {e}")
        X[i,] = np.zeros((*self.target_size, 3))
    y = batch_df[self.label_cols].values
    return X, y

  def on_epoch_end(self):
    if not self.is_validation:
      self.resample_indices()

  def resample_indices(self):
    self.resampled_indices = []
    y_labels = np.argmax(self.df[self.label_cols].values, axis=1)
    for class_id in range(len(self.label_cols)):
      class_indices = np.where(y_labels == class_id)[0]
      if len(class_indices) == 0: continue
      if len(class_indices) > self.samples_per_class:
        chosen_indices = np.random.choice(class_indices, self.samples_per_class, replace=False)
      else:
        chosen_indices = np.random.choice(class_indices, self.samples_per_class, replace=True)
      self.resampled_indices.extend(chosen_indices)
    np.random.shuffle(self.resampled_indices)
    print(f"Generador re-muestreado a {len(self.resampled_indices)} muestras.")


BASE_DIR = "Dermatological_AI_Model_Training"
DATASET_PATH = os.path.join(BASE_DIR, "dataset_dermatology")
CSV_PATH = os.path.join(BASE_DIR, "metadata_dermatology.csv")
MODEL_SAVE_DIR = "IA/Dermatological_AI_Model"
LOGS_DIR = os.path.join(MODEL_SAVE_DIR, "logs")
TRAINING_LOGS_DIR = os.path.join(LOGS_DIR, "training")
TEST_LOGS_DIR = os.path.join(LOGS_DIR, "test")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SAMPLES_PER_CLASS = 2000
VALIDATION_SPLIT = 0.2
EPOCHS_TRANSFER_LEARNING = 8
EPOCHS_FINE_TUNING = 25
FINE_TUNE_AT_BLOCK_MOBILENET = 'block_13_expand'
FINE_TUNE_AT_BLOCK_RESNET = 'conv5_block1_1_conv'
SINGLE_MODEL_PATH = os.path.join(MODEL_SAVE_DIR, "MODELO_IA.keras")
PROGRESS_FILE = os.path.join(MODEL_SAVE_DIR, "training_progress.txt")

print("Preparando datos...")
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TRAINING_LOGS_DIR, exist_ok=True)
os.makedirs(TEST_LOGS_DIR, exist_ok=True)
try:
  df = pd.read_csv(CSV_PATH)
except Exception as e:
  print(f"Error reading CSV: {e}")
  exit(1)
all_image_files_set = set(os.listdir(DATASET_PATH))
image_mapping = {}
for image_name in tqdm(df['image'], desc="Verificando imágenes"):
  ext_found = next((ext for ext in ['.jpg', '.jpeg', '.png'] if f"{image_name}{ext}" in all_image_files_set), None)
  if ext_found:
    image_mapping[image_name] = f"{image_name}{ext_found}"
df_filtered = df[df['image'].isin(image_mapping.keys())].copy()
df_filtered['image_with_ext'] = df_filtered['image'].map(image_mapping)
label_columns = df_filtered.drop(columns=['image', 'image_with_ext']).columns.tolist()
num_classes = len(label_columns)
print(f"Filtered dataset size: {len(df_filtered)}, Classes: {num_classes}")
train_df, val_df = train_test_split(df_filtered, test_size=VALIDATION_SPLIT, random_state=42)
augmentor = tf.keras.preprocessing.image.ImageDataGenerator(rotation_range=20, width_shift_range=0.1,
                                                            height_shift_range=0.1, shear_range=0.1, zoom_range=0.1,
                                                            horizontal_flip=True, fill_mode='nearest')
train_generator = BalancedDataGenerator(df=train_df, label_cols=label_columns, image_dir=DATASET_PATH,
                                        batch_size=BATCH_SIZE, target_size=IMG_SIZE, augmentor=augmentor,
                                        is_validation=False, samples_per_class=SAMPLES_PER_CLASS)
val_generator = BalancedDataGenerator(df=val_df, label_cols=label_columns, image_dir=DATASET_PATH,
                                      batch_size=BATCH_SIZE, target_size=IMG_SIZE, augmentor=None, is_validation=True)
print("Datos y generadores listos.")

print("Verificando modelo previo...")


def read_progress():
  if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r') as f:
      return f.read().strip()
  return "none"


def save_progress(phase):
  with open(PROGRESS_FILE, 'w') as f:
    f.write(phase)


training_progress = read_progress()

if os.path.exists(SINGLE_MODEL_PATH):
  print(f"Cargando modelo desde: {SINGLE_MODEL_PATH}")
  try:
    model = load_model(SINGLE_MODEL_PATH)
    if training_progress in ["none", "transfer_incomplete"]:
      current_phase = "transfer"
    elif training_progress in ["transfer_complete", "finetune_incomplete"]:
      current_phase = "finetune"
    else:
      current_phase = "done"
  except Exception as e:
    print(f"Error loading model: {e}")
    current_phase = "transfer"
    save_progress("transfer_incomplete")
else:
  print("Construyendo nuevo modelo...")
  input_tensor = Input(shape=(*IMG_SIZE, 3))
  mobilenet_base = MobileNetV2(weights='imagenet', include_top=False, input_tensor=input_tensor)
  mobilenet_output = GlobalAveragePooling2D()(mobilenet_base.output)
  resnet_base = ResNet50(weights='imagenet', include_top=False, input_tensor=input_tensor)
  resnet_output = GlobalAveragePooling2D()(resnet_base.output)
  resnet_dense = Dense(512, activation='relu')(resnet_output)
  resnet_dense = Dropout(0.4)(resnet_dense)
  resnet_dense = Dense(256, activation='relu')(resnet_dense)
  resnet_dense = Dropout(0.3)(resnet_dense)
  combined = Concatenate()([mobilenet_output, resnet_dense])
  x = Dense(512, activation='relu')(combined)
  x = Dropout(0.5)(x)
  x = Dense(256, activation='relu')(x)
  x = Dropout(0.3)(x)
  output = Dense(num_classes, activation='sigmoid')(x)
  model = Model(inputs=input_tensor, outputs=output)
  for layer in mobilenet_base.layers:
    layer.trainable = False
  for layer in resnet_base.layers:
    layer.trainable = False
  current_phase = "transfer"
  save_progress("transfer_incomplete")

if current_phase == "transfer":
  print("FASE 1: Transfer Learning...")
  model.compile(optimizer=Adam(), loss='binary_crossentropy', metrics=['binary_accuracy'])
  checkpoint_callback = ModelCheckpoint(
    filepath=SINGLE_MODEL_PATH,
    monitor="val_binary_accuracy",
    save_best_only=True,
    verbose=1,
    mode='max'
  )
  log_dir = os.path.join(TRAINING_LOGS_DIR, datetime.now().strftime("%Y%m%d-%H%M%S"))
  tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)
  try:
    model.fit(
      train_generator,
      validation_data=val_generator,
      epochs=EPOCHS_TRANSFER_LEARNING,
      callbacks=[checkpoint_callback, tensorboard_callback, TqdmCallback(verbose=2)]
    )
    model = load_model(SINGLE_MODEL_PATH)
    save_progress("transfer_complete")
    print("FASE 1 completada.")
    current_phase = "finetune"
  except Exception as e:
    print(f"Error during Transfer Learning: {e}")
    save_progress("transfer_incomplete")
    exit(1)

if current_phase == "finetune":
  print("FASE 2: Fine-Tuning...")
  fine_tune_from_this_layer = False
  for layer in model.layers:
    if layer.name == FINE_TUNE_AT_BLOCK_MOBILENET or layer.name == FINE_TUNE_AT_BLOCK_RESNET:
      fine_tune_from_this_layer = True
    if fine_tune_from_this_layer:
      layer.trainable = True
  model.compile(optimizer=Adam(learning_rate=1e-5), loss='binary_crossentropy', metrics=['binary_accuracy'])
  checkpoint_callback = ModelCheckpoint(
    filepath=SINGLE_MODEL_PATH,
    monitor="val_binary_accuracy",
    save_best_only=True,
    verbose=1,
    mode='max'
  )
  early_stopping = EarlyStopping(monitor='val_loss', patience=5, verbose=1, restore_best_weights=True)
  reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, verbose=1)
  log_dir = os.path.join(TRAINING_LOGS_DIR, datetime.now().strftime("%Y%m%d-%H%M%S"))
  tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)
  try:
    model.fit(
      train_generator,
      validation_data=val_generator,
      epochs=EPOCHS_FINE_TUNING,
      callbacks=[checkpoint_callback, early_stopping, reduce_lr, tensorboard_callback, TqdmCallback(verbose=2)]
    )
    save_progress("finetune_complete")
    print("FASE 2 completada.")
  except Exception as e:
    print(f"Error during Fine-Tuning: {e}")
    save_progress("finetune_incomplete")
    exit(1)

print(f"Modelo guardado en: {SINGLE_MODEL_PATH}")
print("Entrenamiento finalizado.")
