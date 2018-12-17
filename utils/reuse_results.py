import pickle
import os
from configuration import Configuration as cfg
from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_curve, auc as compute_auc


def load_results(test_dir = cfg.log_dir + "test/", experiment_name = cfg.experiment_name):

    assert(os.path.exists(test_dir))
    
    files = [filename for filename in os.listdir(test_dir) if "result_p" in filename]
    
    results = []
    for filename in files:
        percentage = int(filename.replace("result_p","").replace(".pkl",""))
        with open(test_dir+filename,'rb') as file:
            result = pickle.load(file)
        results.append((percentage,result))
    
    return results

def get_performance_metrics(test_dir = cfg.log_dir + "test/", experiment_name = cfg.experiment_name):

    results = load_results(test_dir, experiment_name)
    output_str = []
    for y in results:
        y_output_str = ""
        percentage = y[0]
        result = y[1]
        y_true = [x[0] for x in result]
        y_scores = [x[1] for x in result]
        y_output_str += "Percentage of outliers: %d\n"%percentage
        if cfg.auroc:
            AUROC = roc_auc_score(y_true, y_scores)
            y_output_str += "\tAUROC:\t%.5f\n"%AUROC

        if cfg.auprc:
            pr, rc, _ = precision_recall_curve(y_true, y_scores)
            AUPRC = compute_auc(rc,pr)
            y_output_str += "\tAUPRC:\t%.5f\n"%AUPRC
        output_str.append(y_output_str)

    return output_str

def export_scores(test_dir = cfg.log_dir + "test/", experiment_name = cfg.experiment_name, dataset = cfg.dataset):

    if cfg.training_mode == "GPND_default":
        alg_name = "GPND"
    elif cfg.training_mode.lower() == "autoencoder":
        alg_name = "GPND_AE"

    result = load_results(test_dir, experiment_name)[0][1]
    labels = [x[0] for x in result]
    scores = [x[1] for x in result]
    pickle.dump([scores,labels],open('/home/exjobb_resultat/data/%s_%s.pkl'%(dataset,alg_name),'wb'))
    print("Exported results to '/home/exjobb_resultat/data/%s_%s.pkl'"%(dataset,alg_name))
    # Update data source dict with experiment name
    common_results_dict = pickle.load(open('/home/exjobb_resultat/data/name_dict.pkl','rb'))

    common_results_dict[dataset][alg_name] = experiment_name
    pickle.dump(common_results_dict,open('/home/exjobb_resultat/data/name_dict.pkl','wb'), protocol=2)
    print("Updated entry ['%s']['%s'] = '%s' in file /home/exjobb_resultat/data/name_dict.pkl"%(dataset,alg_name,experiment_name))
