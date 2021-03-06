from utils import loadbdd100k
from pathlib import Path

class Configuration(object):


    # Neural network architecture options 
    # How to specify architecture: (order of numbers in string, separated by "_" as A_B_C_...)
    # A: use_maxpool = #1 or 0
    # B: n_conv
    # C: n_dense
    # D: channels out of first conv. layer
    # E: zsize, dimension of latent vector
    # F: filter size 
    # G: stride 
    # H: pad

    dataset = "prosivic"
    experiment_name = "GPND_common_architecture_181217"
    log_dir = './log/' + dataset + '/' + experiment_name + '/'
    export_results = False
    # Diagnostics
    sample_size = 16
    sample_rows = 4 # nrow to save_image grid
    loss = "bce"
    # Testing options
    nd_original_GPND = False
    percentages = [50] # percentage of outliers to use during testing
    auroc = True
    auprc = True
    plot_roc = True
    plot_prc = True

    # dataset specific options below
    if dataset == "prosivic":
        training_mode = ("autoencoder","GPND_default")[1] # Options: "autoencoder", "GPND_default"
        # Hyperparameters
        betas = (0.5,0.999) # adam solver standard is (0.5, 0.999), GPND standard is (0.9,0.999)
        n_train_epochs = 500
        n_epochs_between_lr_change = int(n_train_epochs * 1/2)
        lr_drop_factor = 10
        num_sample_epochs = 10
        lr_g  = 0.001
        lr_e  = 0.001
        lr_d  = 0.001
        lr_ge = 0.001
        lr_zd = 0.001
        rec_loss_weight = 1
        weight_g_loss = 1
        #architecture = "0_4_0_16_256_4_2_1"
        architecture = "0_5_1_16_512_5_2_2"
        n_dense_units = None
        inliers_name = "sunny"
        outliers_name = "foggy"
        zd_n_layers = 3
        zd_out_units = [256,256,1]

        # Dataset options
        image_height = 256
        image_width = 256
        channels = 3
        model_name = "_".join([inliers_name, architecture])

        batch_size = 64
        test_batch_size = 8 # Jacobian computations require smaller batches
        use_batchnorm = True
        data_div = 1
        n_train = 6785 // data_div
        n_val = 840 // data_div
        n_test = 500*2 // data_div # for GPND algorithm, the test set is split into val and test set during testing, since the valset contains outliers in order to compute an optimal threshold. This is used to compute some of the output values, but not AUPRIN or AUROC, which are threshold independent.
        n_test_in = 500 // data_div

        img_folder =   "../weather_detection_data/prosivic/"
        train_folder = "../weather_detection_data/prosivic/train/"
        val_folder =   "../weather_detection_data/prosivic/val/"
        test_in_folder =  "../weather_detection_data/prosivic/test/in/"
        test_out_folder =  "../weather_detection_data/prosivic/test/out/foggy/"


    elif dataset == "dreyeve":
        training_mode = ("autoencoder","GPND_default")[1]
        architecture = "0_6_1_16_512_5_2_2"
        inliers_name = "sunny_highway"
        outliers_name = "rainy_highway"
        n_dense_units = None
        zd_n_layers = 3
        zd_out_units = [256,256,1]

        image_height = 256
        image_width = 256
        channels = 3
        model_name = "_".join([inliers_name, architecture])

        use_batchnorm = True

        # Hyperparameters
        betas = (0.5,0.999) # adam solver standard is (0.5, 0.999), GPND standard is (0.9,0.999)
        n_train_epochs = 500
        n_epochs_between_lr_change = int(n_train_epochs * 1/2)
        lr_drop_factor = 10
        num_sample_epochs = 10
        batch_size = 64
        test_batch_size = 8 # Jacobian computations require smaller batches
        lr_g = 0.001
        lr_e = 0.001
        lr_d = 0.001
        lr_ge = 0.001
        lr_zd = 0.001
        rec_loss_weight = 1
        weight_g_loss = 1

        # Dataset options
        data_div = 1
        n_train = 6000 // data_div
        n_val = 600 // data_div
        n_test = 1200 // data_div # for GPND algorithm, the test set is split into val and test set during testing, since the valset contains outli$
        n_test_in = 600 // data_div

        img_folder =   "../weather_detection_data/dreyeve/sunny_highway_countryside_morning_evening_vs_rainy_highway_countryside_morning_evening/"
        train_folder = "../weather_detection_data/dreyeve/sunny_highway_countryside_morning_evening_vs_rainy_highway_countryside_morning_evening/train/"
        val_folder =   "../weather_detection_data/dreyeve/sunny_highway_countryside_morning_evening_vs_rainy_highway_countryside_morning_evening/val/"
        test_in_folder =  "../weather_detection_data/dreyeve/sunny_highway_countryside_morning_evening_vs_rainy_highway_countryside_morning_evening/test/in/"
        test_out_folder = "../weather_detection_data/dreyeve/sunny_highway_countryside_morning_evening_vs_rainy_highway_countryside_morning_evening/test/out/"

    elif dataset == "mnist":
        batch_size = 128
        test_batch_size = batch_size # Jacobian computations require smaller batches
        architecture = None
        betas = (0.9,0.999) # GPND standard
        n_train_epochs = 100
        n_epochs_between_lr_change = 40
        num_sample_epochs = 5
        lr_g = 0.002
        lr_e = 0.002
        lr_d = 0.002
        lr_ge = 0.002
        lr_zd = 0.002
        rec_loss_weight = 1

    elif dataset == "bdd100k":
        img_folder = Path("/data/bdd100k/images/train_and_val_256by256")
        norm_file = "/data/bdd100k/namelists/clear_or_partly_cloudy_or_overcast_and_highway_and_daytime.txt"
        norm_filenames = loadbdd100k.get_namelist_from_file(norm_file)
        out_file = "/data/bdd100k/namelists/rainy_or_snowy_or_foggy_and_highway_and_daytime_or_dawndusk_or_night.txt"
        out_filenames = loadbdd100k.get_namelist_from_file(out_file)
        norm_spec = [["weather", ["clear","partly cloudy", "overcast"]],["scene", "highway"],["timeofday", "daytime"]]
        out_spec = [["weather", ["rainy", "snowy", "foggy"]],["scene", "highway"],["timeofday",["daytime","dawn/dusk","night"]]]
# Training logged at Tue, 18 Dec 2018 06:37:07 UTC
# Total training time:	8h5m34.2s
# Average time/epoch:	0m58.27sTesting started at Tue, 18 Dec 2018 06:39:38 UTC
Results for experiment:
Inliers: foggy
Outliers sunny
Percentage of outliers: 50
	AUROC:	0.99196
	AUPRC:	0.99224
	Test time for percentage:	6h30m13.8s
Testing started at Tue, 18 Dec 2018 13:11:18 UTC
Results for experiment:
Inliers: foggy
Outliers sunny
Percentage of outliers: 50
	AUROC:	0.99196
	AUPRC:	0.99224
	Test time for percentage:	0h0m0.0s
Testing started at Sun, 06 Jan 2019 18:28:46 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Testing started at Sun, 06 Jan 2019 18:43:08 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Testing started at Sun, 06 Jan 2019 19:04:28 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Testing started at Sun, 06 Jan 2019 19:05:48 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Testing started at Sun, 06 Jan 2019 19:07:02 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Testing started at Sun, 06 Jan 2019 19:07:53 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.84375
	AUPRC:	0.88058
	Test time for percentage:	0h0m0.0s
Testing started at Sun, 06 Jan 2019 19:08:14 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.84375
	AUPRC:	0.88058
	Test time for percentage:	0h0m0.0s
Testing started at Sun, 06 Jan 2019 19:09:18 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.84375
	AUPRC:	0.88058
	Test time for percentage:	0h0m0.0s
Testing started at Sun, 06 Jan 2019 19:12:16 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.95476
	AUPRC:	0.95410
	Test time for percentage:	5h55m33.4s
Testing started at Mon, 07 Jan 2019 07:55:13 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	6h53m40.0s
Testing started at Mon, 07 Jan 2019 15:00:05 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
Testing started at Mon, 07 Jan 2019 15:00:35 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.95476
	AUPRC:	0.95410
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:28:17 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.95476
	AUPRC:	0.95410
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:28:41 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:31:45 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:32:51 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:36:17 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
Testing started at Tue, 08 Jan 2019 08:37:40 UTC
Results for experiment:
Inliers: foggy
Outliers: sunny
Percentage of outliers: 50
	AUROC:	0.02076
	AUPRC:	0.30759
	Test time for percentage:	0h0m0.0s
