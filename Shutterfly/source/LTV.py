from dateutil.parser import parse as date_parser
from dateutil import rrule
from datetime import timedelta
import sys

class LTV:
    def __init__(self, input_file, output_file, show_X_customers=10):
        customer_info = {}
        self.read_from_file(input_file, customer_info)
        top_LTVs = self.topXLTVCustomers(int(show_X_customers), customer_info)
        self.output_to_file(output_file, top_LTVs)
        print("\nData saved in: {}".format(output_file))

    def total_weeks(self, start, end):
        # get previous sunday
        start = start - timedelta((start.weekday() + 1) % 7)
        # get next saturday
        end = end - timedelta(((end.weekday() + 1) % 7) - 6)
        #gets number of weeks
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start, until=end)
        return weeks.count()

    # This functions will read each line from file and ingest the data into D
    def read_from_file(self, file_path, events):
        first_loop = True
        with open(file_path) as f:
            for line in f.readlines():
                if first_loop:
                    first_loop = False
                    line_eval = line.strip()[1:-1]
                else:
                    line_eval = line.strip()[:-1]
                self.ingest(line_eval, events)

    def output_to_file(self, fname, data):
        with open(fname, 'w') as f:
            f.write('Customer_ID, LTV_value' + '\n')
            for x in data:
                f.write(x[0] + ', ' + str(x[1]) + '\n')

    # ingest all data into a python dict.
    # each 'key' represents a customer and 'value' is a list of all events for that customer
    def ingest(self, e, D):
        dic = eval(e)

        if 'event_time' in dic:
            dic['event_time'] = date_parser(dic['event_time'])


        customer_id = dic['customer_id'] if dic['type'] != 'CUSTOMER' \
                      else dic['key']

        if customer_id not in D:
            D[customer_id] = [dic]
        else:
            D[customer_id].append(dic)

    #This function will get avg value for visits per week
    def calculate_visit_per_week(self, customer_id, D):

        # In case the data is corrupt, no site_visit events present but 'order' events do exist,
        #  then interpret order events as site_visits
        visit_key = 'SITE_VISIT' if 'SITE_VISIT' in [r['type'] for r in D[customer_id]] else 'ORDER'

        #this will create a list of datetime for all 'SITE_VISIT'events for a customer
        visits_date_list = [r['event_time'] for r in D[customer_id] if r['type'] == visit_key]

        if visits_date_list:
            #this will calcuate total active weeks by getting min and max visit date
            active_weeks = self.total_weeks(min(visits_date_list), max(visits_date_list))
            #this will give you number of visits by getting length of the event visit length
            visits_num = float(len(visits_date_list))
            return visits_num / active_weeks

    #This will get you average spending per visit
    def calculate_spending_per_visit(self, customer_id, D, avg_visit_per_week):
        #checks for order type event for each customer_id, if no orders are present for a customer return 0
        if 'ORDER' in [r['type'] for r in D[customer_id]]:

            #get list of orders for each customer
            order_data = [(r['key'], r['verb'], r['event_time'], float(r['total_amount'].split()[0]))
                          for r in D[customer_id] if r['type'] == 'ORDER']
            order_amounts_by_id = {}
            for k, verb, ev_dt, amount in order_data:
                #if order key already exit than check if event date is greater than already present,
                #if its recent than update the amount or ignore it
                #if not exist than add it to list
                if k not in order_amounts_by_id:
                    order_amounts_by_id[k] = (ev_dt, amount)
                else:
                    if ev_dt > order_amounts_by_id[k][0]:
                        order_amounts_by_id[k] = (ev_dt, amount)

            #add all the amounts
            total_order_amounts = sum([order_amounts_by_id[k][1] for k in order_amounts_by_id])
            #divide total order amount by avg visit per week
            avg_spending_per_visit = float(total_order_amounts) / avg_visit_per_week

            return avg_spending_per_visit * avg_visit_per_week
        else:
            return 0

    def topXLTVCustomers(self, x, D):
        LTVs = []

        for customer_id in D:
            #calculate avg visit per week
            avg_visit_per_week = self.calculate_visit_per_week(customer_id, D)
            # calculate avg customer value per week
            avg_cust_val_p_week = self.calculate_spending_per_visit(customer_id, D, avg_visit_per_week)
            #Avg customer lifespan provided by You
            cust_lifespan = 10

            LTVs.append((customer_id,52 * avg_cust_val_p_week * cust_lifespan))

        #sorts the customer on top LTV value
        LTVs.sort(reverse=True, key=lambda y: y[1])

        #returns x number of customers provided dynamically
        return LTVs[:x]



