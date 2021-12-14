import csv


class csv_data_export():
    def __init__(self):
        
        
    def _append_to_csv(path_folder, csv_filename, csv_headers, data_to_append):
    path__ = path_folder + csv_filename
    no_headers = not os.path.exists(path__) or os.stat(path__).st_size == 0
    with open(csv_filename, 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        if no_headers:
            writer.writerow(csv_headers)
        writer.writerow(data_to_append)
