def histogram_of_dates(dates, plot_dir, save=False):
        min_dates = []
        for person in dates:
                min_dates.append(min(dates[person]))

        plt.hist(min_dates, bins=len(list(set(min_dates))))
        plt.title("Histogram of Minimum Dates")
        if save:
                plt.savefig(plot_dir+"min_date_hist.png")
        else:
                plt.show()

        plt.clf()

        max_dates = []
        for person in dates:
                max_dates.append(max(dates[person]))

        plt.hist(max_dates, bins=len(list(set(max_dates))))
        plt.title("Histogram of Maximum Dates")
        if save:
                plt.savefig(plot_dir+"max_date_hist.png")
        else:
                plt.show()

        return dates
