# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from urllib import response
from actions import finance_api

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, UserUttered, ActionExecuted, ActiveLoop, EventType


class ValidateCompanyForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_company_form"

    def validate_company(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:     
        # TODO: capture more intents here. Do not include company_info unless you change nlu pattern
        print("Validating", slot_value)
        if tracker.latest_message['intent']['name'] == "deny": # and tracker.latest_message['intent']['confidence'] >= 0.7
            return {"requested_slot": None, "company": None}

        if len(slot_value.split(" ")) > 1:
            dispatcher.utter_message(text="Sorry, I can't find such company. Please repeat")
            return {"company": None}
        else:
            print("Validation ok")
            return {"company": slot_value}

class ValidatePlotTypeForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_plot_type_form"

    @staticmethod
    def plots_db() -> List[Text]:
        """Database of supported plot types"""
        return ["candle", "line"]

    def validate_plot_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate plot type value."""

        if slot_value.lower() in self.plots_db():
            return {"plot_type": slot_value}
        else:
            # validation failed, set this slot to None so that the user will be asked for the slot again
            return {"plot_type": None}




name_symbol_mapper = {}
class ActionGetStockValues(Action):
    def name(self) -> Text:
        return "get_stock_value"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionGetStockValues")
        company_name = tracker.get_slot("company")
        if company_name.lower() not in name_symbol_mapper:
            company_symbol , ambiguity = finance_api.get_symbol_from_name(company_name, debug=False)
            if ambiguity:
                print("Ambuigity for ", company_name)
            name_symbol_mapper[company_name.lower()] = company_symbol

        value, full_name, currency = finance_api.get_value_from_symbol(name_symbol_mapper[company_name.lower()], debug=False)
        return [SlotSet("company_symbol", name_symbol_mapper[company_name.lower()]), 
                SlotSet("company_stock_value", value),
                SlotSet("currency", currency)]

class ActionSendTelegramPlot(Action):
    def name(self) -> Text:
        return "send_stock_value_plot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionSendTelegramPlot")
        company_name = tracker.get_slot("company")
        assert company_name.lower() in name_symbol_mapper, "Company symbol not known"
        
        data = finance_api.get_past_values_from_symbol(name_symbol_mapper[company_name.lower()], debug=True)
        print("Plot type: ", tracker.get_slot("plot_type"))
        plot_path = finance_api.create_past_values_plot(data, company_name, type=tracker.get_slot("plot_type"))
        finance_api.send_plot_telegram(plot_path, message="Here the plot that you requested:")
        return []

class ActionPredictTrend(Action):
    def name(self) -> Text:
        return "predict_stock_trend"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionPredictTrend")
        dispatcher.utter_message(text=f"Analyzing past performances...")
        company_name = tracker.get_slot("company")
        if company_name.lower() not in name_symbol_mapper:
            company_symbol , ambiguity = finance_api.get_symbol_from_name(company_name, debug=False)
            if ambiguity:
                print("Ambuigity for ", company_name)
            name_symbol_mapper[company_name.lower()] = company_symbol
        
        data = finance_api.get_past_values_from_symbol(name_symbol_mapper[company_name.lower()], debug=True)
        trend = finance_api.predict_trend(data, debug=False)
        trend = "positive" if trend >= 0 else "negative"
        dispatcher.utter_message(text=f"The current trend of {company_name} is {trend}")
        return []

class ActionClearCompanyWMsg(Action):
    def name(self) -> Text:
        return "clear_company_with_msg"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("Clearing company w msg")
        dispatcher.utter_message(text="Sorry, if it was wrong, let me clean my memory. Please continue...")
        return [SlotSet("company", None)]

class ActionClearCompany(Action):
    def name(self) -> Text:
        return "clear_company"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("Clearing company without msg")
        return [SlotSet("company", None)]

class SavedAskedCompany(Action):
    """
        Save into 'companies_stock_asked' the current company for which the user has already asked stock updates
        'companies_stock_asked' is used in order not to ask the user whether it want further details on a company, if it has already asked stock updates
    """
    def name(self) -> Text:
        return "save_asked_company"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        val = tracker.get_slot("companies_stock_asked")
        company = tracker.get_slot("company")
        
        if val is None:
            val = []
        val.append(company)
        print("List of companies: ", val)
        return [SlotSet("companies_stock_asked", val)]

class ActionAskWantStock(Action):
    """
        In case the company was not just added, ask wheteher the user is interested in the stock value of the company
    """
    def name(self) -> Text:
        return "ask_want_stock"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        val = tracker.get_slot("companies_stock_asked")
        company = tracker.get_slot("company")
        if val is None or company not in val:
            dispatcher.utter_message(text="Do you want to have also some news about its stock value?")
        return []

cached_company_news = []
cached_last_news_shown = []
class ActionGetNews(Action):
    def name(self) -> Text:
        return "search_company_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionGetNews")
        global cached_company_news
        global cached_last_news_shown
        company_name = tracker.get_slot("company")
        
        data = finance_api.get_company_news(company_name)
        if len(data) == 0:
            dispatcher.utter_message(text="No news where found")
            return []

        dispatcher.utter_message(text="The first three news found on The Guardian will follow:")
        dispatcher.utter_message(text="")

        cached_company_news = data
        n = 0
        for news in cached_company_news[:3]:
            dispatcher.utter_message(text=f"{n+1}. {news['pillarName']}: {news['webTitle']}")
            dispatcher.utter_message(text=f"")
            n += 1
        cached_last_news_shown.extend(cached_company_news[:3].copy())
        del cached_company_news[:n]
        return []

class ActionSendNewsLinks(Action):
    def name(self) -> Text:
        return "send_news_link"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionSendNewsLinks")
        global cached_last_news_shown
        assert cached_last_news_shown != []

        for news in cached_last_news_shown[-3:]:
            finance_api.send_message_telegram(f"{news['pillarName']}: {news['webTitle']}\n {news['webUrl']}")
        cached_last_news_shown = []
        return []




class ActionGetCompanyInfo(Action):
    def name(self) -> Text:
        return "get_company_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("ActionGetCompanyInfo")
        company_name = tracker.get_slot("company")
        
        info = finance_api.get_company_info(company_name.lower())
        dispatcher.utter_message(text=info)
        return []


class ActionGetBestIndex(Action):
    def name(self) -> Text:
        return "get_best_index"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        symbol , name , change = finance_api.get_best_index()
        dispatcher.utter_message(text=f"{name} ({symbol}) registers an increase of {change}%")
        return []

class ActionGetWorstIndex(Action):
    def name(self) -> Text:
        return "get_worst_index"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        symbol , name , change = finance_api.get_worst_index()
        dispatcher.utter_message(text=f"{name} ({symbol}) registers a decrease of {-change}%")
        return []

class ActionSaveFeedback(Action):
    def name(self) -> Text:
        return "save_feedback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("save_feedback")
        if tracker.latest_message['intent']['name'] == "deny":
            dispatcher.utter_message(text=f"Cancelling the action. What do you want to do next?")
            return [SlotSet("feedback", None)]

        msg = tracker.get_slot("feedback")
        with open("data/feedbacks.txt", "a") as myfile:
            myfile.write(msg + "\n")

        dispatcher.utter_message(text=f"Thank you for helping us! We will forward the message to the developers")
        return [SlotSet("feedback", None)]