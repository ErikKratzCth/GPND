import pickle
import os
from configuration import Configuration as cfg
from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_curve, auc as compute_auc


def load_results(test_dir = cfg.log_dir + "test/", experiment_name = cfg.experiment_name):

    assert(os.path.exists(test_dir))
    
    files = [filename for filename in os.listdir(test_dir) if experiment_name+"_result_p" in filename]
    
    results = []
    for filename in files: 
        percentage = int(filename.replace(experiment_name+"_result_p","").replace(".pkl",""))
        with open(test_dir+filename,'rb') as file:
            result = pickle.load(file)
        results.append((percentage,result))
    
    return results

def get_performance_metrics(test_dir = cfg.log_dir + "test/", experiment_name = cfg.experiment_name):
    output_str = "Result for experiment:\n"
    output_str += "Inliers: %s\n"%cfg.outliers_name
    output_str += "Outliers %s\n"%cfg.inliers_name

    results = load_results(test_dir, experiment_name)

    for y in results:
        percentage = y[0]
        result = y[1]
        y_true = [x[0] for x in result]
        y_scores = [x[1] for x in result]
        output_str += "\tPercentage of outliers: %d\n"%percentage
        if cfg.auroc:
            AUROC = roc_auc_score(y_true, y_scores)
            output_str += "\tAUROC:\t%.5f\n"%AUROC

        if cfg.auprc:
            pr, rc, _ = precision_recall_curve(y_true, y_scores)
            AUPRC = compute_auc(rc,pr)
            output_str += "\tAUPRC:\t%.5f\n"%AUPRC

    return output_str
