from .class_ComponentABC import Component
from .class_ConfigStorage import class_ConfigStorage
import importlib
from io import BytesIO
import json
import os
import difflib
import requests
from importlib import metadata
import subprocess
from urllib.request import urlopen
from zipfile import ZipFile
from threading import Thread
import traceback


class Composite(Component):
    """
    The Composite class represents the complex components that may have
    children. Usually, the Composite objects delegate the actual work to their
    children and then "sum-up" the result.
    """

    def __init__(self, _uid, _conf=None) -> None:
        self._uid = _uid
        self._conf = _conf
        self._children: List[Component] = []
        self._methods = []
        self._references = {}
        self._tools = []

    """
    A composite object can add or remove other components (both simple or
    complex) to or from its child list.
    """

    def add(self, component: Component) -> None:
        self._children.append(component)
        component.parent = self

    def remove(self, component: Component) -> None:
        self._children.remove(component)
        # component.parent = None

    def subscribe(self, publisher, subscriber, subscriberMethod):
        # Create unique identifier for subscription
        identifier = publisher + subscriber + subscriberMethod

        # Get objects based on their names
        if type(subscriber) is str:
            subscriber = self.getChild(subscriber)
        if type(publisher) is str:
            publisher = self.getChild(publisher)
        subscriberMethod = getattr(subscriber, subscriberMethod)

        # Add subscription and check for duplicates
        try:
            handler_dict = {identifier: subscriberMethod}
            if identifier not in publisher._event._Event__eventhandlers:
                publisher._event += handler_dict
                return f"{publisher._id} added subscriber {subscriber._id} with method {subscriberMethod}"
            else:
                return f"Detected duplicate subscription! Ignoring {publisher._id} adding subscriber {subscriber._id} with method {subscriberMethod}!"

        except Exception as e:
            traceback.print_exc()

    def unsubscribe(self, publisher, subscriber, subscriberMethod):
        # Create unique identifier for subscription
        identifier = publisher + subscriber + subscriberMethod

        # Get objects based on their names
        if type(subscriber) is str:
            subscriber = self.getChild(subscriber)
        if type(publisher) is str:
            publisher = self.getChild(publisher)
        subscriberMethod = getattr(subscriber, subscriberMethod)

        # Remove subscription and check for duplicates
        try:
            publisher._event -= identifier
            return f"{publisher._id} removed subscriber {subscriber._id} with method {subscriberMethod}"

        except Exception as e:
            traceback.print_exc()

    def describe(self, attribute):
        attribute_list = []
        print(attribute)
        for item in vars(self):
            attribute_list.append(item)

        try:
            value = getattr(self, difflib.get_close_matches(attribute, attribute_list)[0])
            if "children" in attribute:
                return ", ".join(child._id for child in value)
            if "method" in attribute:
                return ", ".join(method for method in value)
            return value
        except:
            return None

    def getConf(self):
        child = self.getChild("ConfigStorage")

        # query for defined id
        myquery = {"_id": self._uid}

        # find one with given id
        mydoc = child.query(myquery)

        mydoc.pop("_id", None)
        self._conf = mydoc

    def getChild(self, name):
        for child in self._children:
            if child._id == name:
                return child
        return None

    def get_installed_packages(self):
        # prevent race condition with the command below before importing
        importlib.invalidate_caches()
        return [pkg.metadata["Name"] for pkg in metadata.distributions()]

    def generate_requirements(self, directory):
        try:
            # Run pipreqs command and capture the output
            result = subprocess.run(["pipreqs", "--print", directory], stdout=subprocess.PIPE, text=True)

            # Split the output into lines and store them in a list
            requirements_list = result.stdout.splitlines()

            # Get installed packages
            installed_packages = self.get_installed_packages()
            print("installed_packages")
            print(installed_packages)
            print("requirements_list")
            print(requirements_list)

            # Print the captured output
            print("Requirements generated successfully.")

            # Remove already install packages from requirements_list
            requirements_list = [requirement for requirement in requirements_list if
                                 requirement.split('==')[0] not in installed_packages]

            # Return the list if needed
            return requirements_list

        except subprocess.CalledProcessError as e:
            print(f"Error generating requirements file: {e}")
            return None

    def install_requirements(self, requirements_list):
        try:
            for requirement in requirements_list:
                subprocess.run(["pip", "install", requirement], check=True)
                print(f"Installed: {requirement}")

            print("All requirements installed successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")

    def impModule(self, item):
        modules_conf = self._conf

        # dynamic class loading with error handling for not contained classes
        try:
            globals()[item] = getattr(importlib.import_module("Modules." + item), item)
            self.instantiateObject(item, modules_conf)

        except:
            """add code to ask DTPS for class"""
            print("I need " + item + " first. So I'll ask the DTPS to provide it!")
            url = "http://dtps-svc.dt.svc.cluster.local:8000/provide/" + item
            with urlopen(url) as zipresp:
                with ZipFile(BytesIO(zipresp.read())) as zfile:
                    for file in zfile.namelist():
                        print(file)
                        if ".py" in file:
                            zfile.extract(file, './Modules')
                        elif ".json" in file:
                            zfile.extract(file, './Descriptions')

            # Check and install requirements if needed
            self.install_requirements(self.generate_requirements("./Modules"))

            # prevent race condition with the command below before importing
            importlib.invalidate_caches()
            globals()[item] = getattr(importlib.import_module("Modules." + item), item)
            self.instantiateObject(item, modules_conf)

    def unimpModule(self, item):
        # at the moment just here to pass through adapt in future to remove module if possibles
        self.disembodyObject(item)

    def addMethodNames(self, item):
        print(item)
        itemConf = self._conf[item]
        print(itemConf)
        for instance in itemConf:
            # Get child and a list of all attributes
            child = self.getChild(itemConf[instance]["_id"])
            all_attributes = dir(child)

            # Filter out only the methods (those that don't start with '__')
            method_names = [attr for attr in all_attributes if
                            callable(getattr(child, attr)) and not attr.startswith('__')]

            # Add methods to self.methods
            self._methods.extend(method_names)

    def removeMethodNames(self, item):
        print(item)
        itemConf = self._conf[item]
        print(itemConf)
        for instance in itemConf:
            # Get child and a list of all attributes
            child = self.getChild(itemConf[instance]["_id"])
            all_attributes = dir(child)

            # Filter out only the methods (those that don't start with '__')
            method_names = [attr for attr in all_attributes if
                            callable(getattr(child, attr)) and not attr.startswith('__') and not attr.startswith('_')]

            # Remove methods from self.methods
            for method in method_names:
                self._methods.remove(method)

    def instantiateObject(self, item, modules_conf):
        # get configuration
        conf = modules_conf[item]

        # get child_ids to prevent duplicates
        child_ids = []
        for child in self._children:
            child_ids.append(child._id)

        # get className
        className = globals()[item]
        for item in conf:
            if conf[item]["_id"] not in child_ids:
                print("This is the item in conf: " + item)
                itemConf = conf[item]
                print("This is the itemConf: " + str(itemConf))
                if itemConf != "":
                    module = className(itemConf)
                else:
                    module = className()
                self.add(module)

    def disembodyObject(self, item):
        print("removing")

    def learn(self):
        # get old conf
        oldConf = self._conf

        # update Conf from Congiguration Storage
        self.getConf()

        # get modules to learn and to remove
        items_to_learn, items_to_relearn, items_to_remove = self.deep_dict_compare_and_cleanup(oldConf, self._conf)

        learnd = {}
        relearned = {}
        removed = {}

        # prepare return output
        for item in items_to_learn:
            items = []
            if item != {}:
                for subitem in items_to_learn[item]:
                    items.append(items_to_learn[item][subitem]["_id"])
            learnd[item] = items
        for item in items_to_relearn:
            items = []
            if item != {}:
                for subitem in items_to_relearn[item]:
                    items.append(items_to_relearn[item][subitem]["_id"])
            relearned[item] = items
        for item in items_to_remove:
            items = []
            if item != {}:
                for subitem in items_to_remove[item]:
                    items.append(items_to_remove[item][subitem]["_id"])
            removed[item] = items

        # learn new
        self.learn_add(items_to_learn)

        # relearn
        # remove children first
        self.learn_remove(items_to_relearn)
        self.learn_add(items_to_relearn)

        # remove old
        routers = self.learn_remove(items_to_remove)

        print(f"learned: {learnd}")
        print(f"relearnd: {relearned}")
        print(f"removed: {removed}")
        return {"learnd": learnd, "relearned": relearned, "removed": removed, "routers": routers}

    def learn_add(self, items_to_learn):
        try:
            # add objects based on config
            for item in items_to_learn:
                # import modules
                self.impModule(item)

            # add method names
            for item in items_to_learn:
                self.addMethodNames(item)

                # get tools from items to learn for function calling
                with open(f"./Descriptions/{item}.json", "r") as file:
                    class_description = json.load(file)
                    for function in class_description:
                        self._tools.append(class_description[function])

            for item in items_to_learn:
                for instance in items_to_learn[item]:
                    child = self.getChild(items_to_learn[item][instance]["_id"])
                    if hasattr(child, "run"):
                        if hasattr(child, "threading"):
                            th = Thread(target=child.run)
                            th.start()
                        else:
                            child.run()
                    if hasattr(child, "_subscribers"):
                        for subscriber in child._subscribers:
                            # Subscriber x with method y!
                            subscriberMethod = child._subscribers[subscriber]
                            subscriptiontext = self.subscribe(child._id, subscriber, subscriberMethod)
                            print(subscriptiontext)
                    if hasattr(child, "_subscriptions"):
                        for subscription in child._subscriptions:
                            # {_subscriptions: {child to subscribe: method}
                            # Subscribe to x with method y!
                            subscriberMethod = child._subscriptions[subscription]
                            subscriptiontext = self.subscribe(subscription, child._id, subscriberMethod)
                            # add to publishers subscribers
                            print(f"vorher: {self.getChild(subscription)._subscribers}")
                            self.getChild(subscription)._subscribers[child._id] = subscriberMethod
                            print(f"nachher: {self.getChild(subscription)._subscribers}")
                            print(subscriptiontext)
                    # check if added item is listed as subscriber in the children configuration
                    for conf in self._conf:
                        for instance in self._conf[conf]:
                            if "_subscribers" in self._conf[conf][instance]:
                                if item in self._conf[conf][instance]["_subscribers"]:
                                    # Subscriber x with method y!
                                    publisher = self.getChild(self._conf[conf][instance]["_id"])
                                    subscriberMethod = self._conf[conf][instance]["_subscribers"][item]
                                    publisher._subscribers[child._id] = subscriberMethod
                                    subscriptiontext = self.subscribe(publisher._id, item, subscriberMethod)
                                    print(subscriptiontext)
        except Exception as e:
            traceback.print_exc()

    def learn_remove(self, items_to_remove):
        routers = []
        try:

            # remove method names
            for item in items_to_remove:
                self.removeMethodNames(item)

                # remove description from tools
                with open(f"./Descriptions/{item}", "r") as file:
                    class_description = json.load(file)
                    for function in class_description:
                        self._tools.remove(class_description[function])

                # remove description file
                os.remove(f"./Descriptions/{item}.json")

            for item in items_to_remove:
                for instance in items_to_remove[item]:
                    child = self.getChild(items_to_remove[item][instance]["_id"])
                    if hasattr(child, "_subscribers"):
                        for subscriber in child._subscribers:
                            # unsubscriber x with method y!
                            subscriberMethod = child._subscribers[subscriber]
                            subscriptiontext = self.unsubscribe(child._id, subscriber, subscriberMethod)
                            print(subscriptiontext)
                    if hasattr(child, "_subscriptions"):
                        for subscription in child._subscriptions:
                            # unsubscribe to x with method y!
                            subscriberMethod = child._subscriptions[subscription]
                            subscriptiontext = self.unsubscribe(subscription, child._id, subscriberMethod)
                            # remove from publishers subscribers
                            print(f"vorher: {self.getChild(subscription)._subscribers}")
                            self.getChild(subscription)._subscribers.pop(child._id)
                            print(f"nachher: {self.getChild(subscription)._subscribers}")
                            print(subscriptiontext)
                    if hasattr(child, "_router"):
                        routers.append(child._router)
                    # check if removed item is listed as subscriber in the remaining children
                    for ch in self._children:
                        if hasattr(ch, "_subscribers"):
                            # if item in ch._subscribers:
                            if items_to_remove[item][instance]["_id"] in ch._subscribers:
                                # unsubscriber x with method y!
                                subscriber = items_to_remove[item][instance]['_id']
                                subscriberMethod = ch._subscribers[items_to_remove[item][instance]["_id"]]
                                # self.unsubscribe(ch, items_to_remove[item][instance]["_id"], subscriberMethod)
                                subscriptiontext = self.unsubscribe(ch._id, items_to_remove[item][instance]["_id"],
                                                                    subscriberMethod)
                                ch._subscribers.pop(items_to_remove[item][instance]["_id"])
                                print(subscriptiontext)
                    self.remove(child)
        except Exception as e:
            traceback.print_exc()
        return routers

    def deep_dict_compare_and_cleanup(self, old_dict, new_dict):
        def deep_dict_compare(old_dict, new_dict):
            items_to_learn = {}
            items_to_remove = {}

            for key in set(old_dict) | set(new_dict):
                if key in old_dict and key in new_dict:
                    if isinstance(old_dict[key], dict) and isinstance(new_dict[key], dict):
                        sub_learn, sub_remove = deep_dict_compare(old_dict[key], new_dict[key])
                        if sub_learn or sub_remove:
                            items_to_learn[key] = sub_learn
                            if key not in new_dict:
                                items_to_remove[key] = sub_remove
                    elif old_dict[key] != new_dict[key]:
                        items_to_learn[key] = new_dict[key]
                        items_to_remove[key] = old_dict[key]
                elif key in old_dict:
                    items_to_remove[key] = old_dict[key]
                else:
                    items_to_learn[key] = new_dict[key]

            # Clean up empty class entries
            items_to_learn = {k: v for k, v in items_to_learn.items() if v != {}}
            items_to_remove = {k: v for k, v in items_to_remove.items() if v != {}}

            return items_to_learn, items_to_remove

        def deep_dict_cleanup(items_to_learn, items_to_remove, old_dict, new_dict):
            items_to_relearn = {}

            # Detect items to learn
            for item in items_to_learn:
                if item in new_dict and item in old_dict:
                    for subitem in items_to_learn[item]:
                        if subitem in new_dict[item] and subitem in old_dict[item]:
                            if new_dict[item][subitem] != old_dict[item][subitem]:
                                if item not in items_to_relearn:
                                    items_to_relearn[item] = {}
                                items_to_relearn[item][subitem] = new_dict[item][subitem]

            # Clean up empty class entries
            items_to_learn = {k: v for k, v in items_to_learn.items() if v != {}}
            items_to_learn = {k: v for k, v in items_to_learn.items() if k not in items_to_relearn}
            items_to_remove = {k: v for k, v in items_to_remove.items() if v != {}}
            items_to_remove = {k: v for k, v in items_to_remove.items() if k not in items_to_relearn}

            return items_to_learn, items_to_relearn, items_to_remove

        items_to_learn, items_to_remove = deep_dict_compare(old_dict, new_dict)
        items_to_learn, items_to_relearn, items_to_remove = deep_dict_cleanup(items_to_learn, items_to_remove, old_dict,
                                                                              new_dict)

        return items_to_learn, items_to_relearn, items_to_remove

    def process(self):
        # instantiate class_ConfigStorage
        ConfigStorage = class_ConfigStorage()
        self.add(ConfigStorage)

        # get Conf from Congiguration Storage
        self.getConf()
        modules_conf = self._conf

        # add objects based on config
        for item in modules_conf:
            self.impModule(item)

        # get method names
        for item in modules_conf:
            self.addMethodNames(item)

        # get tools from children for function calling
        for description in os.listdir("./Descriptions"):
            with open(f"./Descriptions/{description}", "r") as file:
                class_description = json.load(file)
                for function in class_description:
                    self._tools.append(class_description[function])

        # start child methods
        for child in self._children:
            if hasattr(child, "run"):
                if hasattr(child, "threading"):
                    th = Thread(target=child.run)
                    th.start()
                else:
                    child.run()

        # add subscribtions
        for child in self._children:
            if hasattr(child, "_subscribers"):
                if child._subscribers:
                    for subscriber in child._subscribers:
                        # Subscriber x with method y!
                        subscriberMethod = child._subscribers[subscriber]
                        subscriptiontext = self.subscribe(child._id, subscriber, subscriberMethod)
                        print(subscriptiontext)
            if hasattr(child, "_subscriptions"):
                if child._subscriptions:
                    for subscription in child._subscriptions:
                        # Subscribe to x with method y!
                        subscriberMethod = child._subscriptions[subscription]
                        subscriptiontext = self.subscribe(subscription, child._id, subscriberMethod)
                        # add to publishers subscribers
                        print(f"vorher: {self.getChild(subscription)._subscribers}")
                        self.getChild(subscription)._subscribers[child._id] = subscriberMethod
                        print(f"nachher: {self.getChild(subscription)._subscribers}")
                        print(subscriptiontext)
