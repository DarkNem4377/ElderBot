# xView2 baseline inference — patched for modern Docker/PyPI (TF 1.15 base image)
# Clones upstream baseline inside the image; no local ml/xview2-baseline checkout required.
FROM tensorflow/tensorflow:1.15.5-py3

ENV DEBIAN_FRONTEND=noninteractive

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git python3-opencv \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 999 appuser 2>/dev/null || true && \
    useradd -r -u 999 -g appuser appuser 2>/dev/null || true && \
    mkdir -p /home/appuser/.keras/models && \
    chown -R appuser:appuser /home/appuser

ADD https://github.com/fchollet/deep-learning-models/releases/download/v0.2/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5 \
    /home/appuser/.keras/models/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5

RUN chmod -R 777 /home/appuser/

USER appuser
WORKDIR /home/appuser

RUN mkdir -p ~/code/xview-2/ ~/submission/ ~/output/

# Pin opencv-python to a version that ships a prebuilt cp36 manylinux wheel and
# force pip to prefer binaries, so imgaug's opencv dependency is never compiled
# from source (that source build takes 45+ min on limited CPU).
# keras must be pinned to 2.3.1 — the last multi-backend release. Newer keras
# (2.6+) imports tf.__internal__ (a TF 2.x symbol) and crashes on this TF 1.15
# base; older keras (2.2.x) predates the `callbacks` arg that the baseline's
# damage_inference.py passes to predict_generator. h5py<3 avoids the
# "'str' has no attribute 'decode'" error when loading the old-format .h5 weights.
RUN pip install --user --prefer-binary \
    'opencv-python==4.5.5.64' 'keras==2.3.1' 'h5py<3' \
    matplotlib tqdm libtiff scipy 'Pillow<10' scikit-image \
    imgaug IPython imantics simplification scikit-learn chainer \
    tensorboard tensorboardX && \
    pip install --user 'geopandas<0.11' || pip install --user geopandas

RUN git clone --depth 1 https://github.com/DIUx-xView/xview2-baseline.git ~/code/xview-2

RUN curl -L https://github.com/DIUx-xView/xView2/releases/download/v1.0/localization.h5 \
    -o ~/code/xview-2/weights/localization.h5 && \
    curl -L https://github.com/DIUx-xView/xView2/releases/download/v1.0/classification.hdf5 \
    -o ~/code/xview-2/weights/classification.hdf5

RUN chmod +x ~/code/xview-2/submission/run.sh

ENTRYPOINT ["/home/appuser/code/xview-2/submission/run.sh", "/home/appuser/code/xview-2/"]
