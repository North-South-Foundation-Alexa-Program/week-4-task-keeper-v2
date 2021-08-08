import logging
import ask_sdk_core.utils as ask_utils

import os
import boto3
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.skill_builder import CustomSkillBuilder

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# initialize persistence adapter
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, 
    dynamodb_resource=ddb_resource)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to the Taskkeeper skill. You can ask me to keep track of tasks for you and show outstanding tasks. What would you like to do?"
        handler_input.attributes_manager.session_attributes['launched'] = True
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say something like add task cleaning, mark cleaning as done or show me my tasks?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ShowTasksIntentHandler(AbstractRequestHandler):
    """Handler for Show Tasks Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ShowTasksIntent")(handler_input)

    def handle(self, handler_input):
        
        task_list = handler_input.attributes_manager.persistent_attributes.get("tasks", list())
        
        task_phrases = []
        for task_num, task in enumerate(task_list):
            task_phrases.append(f'task #{task_num+1} is {task}')
        
        task_text = ""
        if len(task_phrases) == 1:
            task_text = task_phrases[0]
        elif len(task_phrases) >= 1:
            task_text = ", ".join(task_phrases[:len(task_phrases)-1]) + " and " + task_phrases[-1]

        if task_text == "":
            speak_output = "Your task list is empty - please add something to it."
        else:
            s_char = "" if len(task_list) == 1 else "s"
            speak_output = f"You have {len(task_list)} task{s_char} in your tasks list: {task_text}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("What else can I help you with?")
                .response
        )

class CreateTaskIntentHandler(AbstractRequestHandler):
    """Handler for Create Tasks Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CreateTaskIntent")(handler_input)

    def handle(self, handler_input):
        
        # task_name = ask_utils.request_util.get_slot(handler_input, "task_name").value
        task_name = handler_input.request_envelope.request.intent.slots["task_name"].value

        task_list = handler_input.attributes_manager.persistent_attributes.get("tasks", list())
        
        if task_name in task_list:
            speak_output = "{} task already exists in your list of tasks,".format(task_name)
        else:
            speak_output = "I added {} to your list of outstanding tasks,".format(task_name)
            task_list.append(task_name)
            attributes_manager = handler_input.attributes_manager
            attributes_manager.persistent_attributes = {'tasks' : task_list }
            attributes_manager.save_persistent_attributes()
            
        s_char = "" if len(task_list) == 1 else "s"
        speak_output = f"{speak_output} you have {len(task_list)} outstanding task{s_char}. "
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("What else can I help you with?")
                .set_should_end_session(not(handler_input.attributes_manager.session_attributes.get('launched', False)))
                .response
        )

class CompleteTaskIntentHandler(AbstractRequestHandler):
    """Handler for Complete Tasks Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CompleteTaskIntent")(handler_input)

    def handle(self, handler_input):
        
        # task_name = ask_utils.request_util.get_slot(handler_input, "task_name").value
        task_name = handler_input.request_envelope.request.intent.slots["task_name"].value
        
        task_list = handler_input.attributes_manager.persistent_attributes.get("tasks", list())        
        
        if task_name in task_list:
            speak_output = "I removed {} from your list of outstanding tasks,".format(task_name)
            task_list.remove(task_name)
            attributes_manager = handler_input.attributes_manager
            attributes_manager.persistent_attributes = {'tasks' : task_list }
            attributes_manager.save_persistent_attributes()
        else:
            speak_output = "I cant find the task named {} in your list of tasks, ask to list your tasks or try again,".format(task_name)

        s_char = "" if len(task_list) == 1 else "s"
        speak_output = f"{speak_output} you have {len(task_list)} outstanding task{s_char}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())

sb.add_request_handler(ShowTasksIntentHandler())
sb.add_request_handler(CreateTaskIntentHandler())
sb.add_request_handler(CompleteTaskIntentHandler())

sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
