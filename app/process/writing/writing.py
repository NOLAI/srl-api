import os
import pandas as pd
import xgboost as xgb
from app.db.models import Essay, WritingProcess
from app.process.writing import liwc, similarity, tscan
from app.process.writing.segment_essay import segment

model = xgb.XGBClassifier()
model.load_model(os.path.join('app', 'process', 'writing', 'all_XGB_model_s2.json'))
LABELS = ['NL', 'COO', 'CV', 'COR', 'CE', 'MM', 'MO', 'ME', 'MP']

async def process_writing(user_id: int, course_id: int):
    essays = await Essay.filter(user_id=user_id, course_id=course_id).order_by('save_time')
    df = pd.DataFrame([{
        'id': essay.id,
        'save_time': int(essay.save_time),
        'essay_content': essay.essay_content,
    } for essay in essays])
    segmented_essays = segment(df)
    if len(segmented_essays) == 0:
        return []

    # Send to LIWC
    liwc_results = liwc.run(segmented_essays)

    # Send to TSCAN
    tscan_results = await tscan.run(segmented_essays)
    tscan_results['cluster_nr'] = tscan_results.index.str.removeprefix('input/').str.removesuffix('.txt').astype(int)

    # Compute similarity features
    similarity_results = await similarity.run(segmented_essays, course_id)

    df_features = pd.merge(tscan_results, liwc_results, on='cluster_nr', how='inner')
    df_features = pd.merge(df_features, similarity_results, on='cluster_nr', how='inner')
    df_features = pd.merge(df_features, segmented_essays, on='cluster_nr', how='inner')
    df_features.columns = df_features.columns.str.strip()

    feature_names = model.get_booster().feature_names
    for col in df_features.columns:
        if col not in feature_names:
            del df_features[col]
    df_features = df_features[feature_names]

    predictions = model.predict(df_features)

    processes = []
    for i, row in df_features.iterrows():
        processes.append(WritingProcess(
            user_id=user_id,
            course_id=course_id,
            process_label=LABELS[predictions[i]],
            start_time=int(row['start_time']),
            end_time=int(row['end_time']),
        ))

    processes.sort(key=lambda x: x.start_time)
    await WritingProcess.bulk_create(processes)
    return processes