# please see readme.md

# To automatically install missing modules, uncomment the following lines of code.
# try:
    # import ModulesValidate
    # ModulesValidate.modulesInstalled(["stashapp-tools", "requests"])
# except Exception as e:
    # import traceback, sys
    # tb = traceback.format_exc()
    # print(f"ModulesValidate Exception. Error: {e}\nTraceBack={tb}", file=sys.stderr)

import sys,os,json
import log
from datetime import datetime
from pathlib import Path
from stashapi.stashapp import StashInterface
from rename import Template, Placeholder, Modifier
from plugin import Plugin

defaultSettings = {
    'debugTracing': False,
    'dryRun': False,
    'renameTemplate': '$(title)'
}

supportedPlaceholders = [
    'studio',
    'title',
    'performers',
    'date',
    'width',
    'height'
]

directoriesToScan = set()

def getStash(jsonInput):
    serverConnection = jsonInput["server_connection"]
    host = serverConnection["Host"]
    if host == "0.0.0.0":
        host = "localhost"
    stashConnection = {
        "Scheme": serverConnection["Scheme"],
        "Host": host,
        "Port": serverConnection["Port"],
    }
    if serverConnection.get("SessionCookie"):
        stashConnection["SessionCookie"] = serverConnection["SessionCookie"]
    if serverConnection.get("ApiKey"):
        stashConnection["ApiKey"] = serverConnection["ApiKey"]
    return StashInterface(stashConnection)


def getSettings(stash, pluginName, defaults):
    settings = defaultSettings.copy()
    try:
        config = stash.call_GQL('query Configuration { configuration { plugins }}')
        plugins_config = config.get('configuration', {}).get('plugins', {})
        if pluginName in plugins_config:
            settings.update(plugins_config[pluginName])
    except Exception:
        pass
    return settings
   

def checkSettings(settings) -> bool:
    global supportedPlaceholders
    template = settings['template']
    
    if len(template.placeholders)==0:
        log.error(f"No placeholders found in Rename Template '{template.pattern}'")
        return False
    
    if 'title' not in [p.name for p in template.placeholders]:
        log.error(f"No 'title' placeholder found in Rename Template '{template.pattern}'")
        return False
    
    for placeholder in template.placeholders:
        if placeholder.name not in supportedPlaceholders:
            log.error(f"Unsupported placeholder '{placeholder.name}' found in Rename Template '{template.pattern}'")
            return False
        
        match placeholder.name:
            case 'studio' | 'title' | 'width' | 'height':
                if len(placeholder.modifiers):
                    log.error(f"Unsupported modifier '{placeholder.modifiers[0].raw}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                    return False
                pass
            case 'performers':
                for modifier in placeholder.modifiers:
                    if not modifier.strict:
                        log.error(f"Unsupported modifier '{modifier.raw}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                        return False
                    match modifier.name:
                        case 'filter':
                            if modifier.value not in ['all','male','female','!male','!female']:
                                log.error(f"Unsupported 'filter' modifier value '{modifier.value}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                        case 'separator':
                            if modifier.value=='':
                                log.error(f"Unsupported 'separator' modifier value '{modifier.value}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                        case _:
                            log.error(f"Unsupported modifier '{modifier.raw}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                            return False
            case 'date':
                if len(placeholder.modifiers)==1:
                    try:
                        format = placeholder.modifiers[0].raw
                        datetime.today().strftime(format)
                    except ValueError:
                        raise ValueError(f"Unsupported format modifier '{placeholder.modifiers[0].raw}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                if len(placeholder.modifiers)>1:
                    log.error(f"Unsupported modifier '{placeholder.modifiers[0].raw}' found on placeholder '{placeholder.name}' in Rename Template '{template.pattern}'")
                pass
            case _:
                log.error(f"Unsupported placeholder '{placeholder.name}' found in Rename Template '{template.pattern}'")
                return False
        
    return True
        

def replaceIllegalChars(filename):
    for ch in ["<", ">", '"', "/", "\\", "|", "?", "*", ":"]:
        filename = filename.replace(ch, "-")
    return filename
   
    
def renameSceneFile(stash, settings, scene, file, nofm):
    global directoriesToScan
    
    template = settings['template']
    dryRun = settings['dryRun']

    id = file.get('id')
    
    basename = file.get('basename')
    path = file.get('path')
    parent = Path(path).parent
    
    filename, extension = os.path.splitext(basename)
    newFilename = template.render(scene, file, nofm)
    newFilename = replaceIllegalChars(newFilename)
    
    if filename == newFilename:
        log.info(f"renameSceneFile(file #{id} '{basename}'): no change")
        return
    
    newBasename = f"{newFilename}{extension}"
    newPath = f"{parent}{os.sep}{newBasename}"
    
    if dryRun:
        log.info(f"renameSceneFile(file #{id} '{basename}'): DRY-RUN rename to '{newBasename}'")
        return
        
    #log.info(f"renameSceneFile(file #{id} '{basename}'): rename... to '{newBasename}'")
    try:
        os.rename(path, newPath)
        log.info(f"renameSceneFile(file #{id} '{basename}'): renamed to '{newBasename}'")
        directoriesToScan.add(f"{parent}")
    except OSError as e:
        log.error(f"renameSceneFile(file #{id} '{basename}'): failed to rename: {e}")

def renameSceneFiles(stash, settings, scene):
    id = scene.get('id')
    title = scene.get('title')
    
    if title == "":
        log.info(f"renameSceneFiles(scene #{id} '{title}') skip due to empty title")
        return
        
    log.info(f"renameSceneFiles(scene #{id} '{title}')")
    files = scene.get('files', [])
    l = len(files)
    for i, file in enumerate(files):
        renameSceneFile(stash, settings, scene, file, (i+1,l))

def renderStudio(placeholder: Placeholder, scene: dict[str,object], file: dict[str,object]) -> str:
    if placeholder.name not in scene:
        return '{missing value}'
        
    studio = scene[placeholder.name]
    
    return studio['name']

def renderPerformers(placeholder: Placeholder, scene: dict[str,object], file: dict[str,object]) -> str:
    if placeholder.name not in scene:
        return '{missing value}'
        
    performers = scene[placeholder.name]
    
    if not isinstance(performers, list):
        return '{not a list}'

    filters: dict[str,Callable[str,bool]] = {
        'all': lambda p: True,
        'male': lambda p: p=='MALE',
        'female': lambda p: p=='FEMALE',
        '!male': lambda p: p!='MALE',
        '!female': lambda p: p!='FEMALE',
    }

    separator: str = ','
    filter = lambda p: True

    modifier: Modifier
    for modifier in placeholder.modifiers:
        if modifier.name == 'separator':
            separator = modifier.value
        if modifier.name == 'filter':
            try:
                filter = filters[modifier.value]
            except KeyError:
                return '{invalid filter}'
    names: list[str] = [p['name'] for p in performers if filter(p['gender'])]
    names.sort()
    return separator.join(names)

def renderDate(placeholder: Placeholder, scene: dict[str,object], file: dict[str,object]) -> str:
    if placeholder.name not in scene:
        return '{missing value}'
        
    value = scene[placeholder.name]

    if not isinstance(value, str):
        return '{not a str}'

    date = datetime.strptime(value, '%Y-%m-%d') # date as supplied by system
    
    format: str = '%Y-%m-%d'
    modifier: Modifier
    for modifier in placeholder.modifiers:
        format = modifier.raw

    return date.strftime(format)


def findLastUpdatedStudio(stash: StashInterface) -> dict:
    query_studio_last_updated = """
        query {
            findStudios(filter:{sort: "updated_at", direction: DESC,page:1,per_page:1}) {
                studios {
                    id
                    name
                    updated_at
                }
            }
        }
    """
    studios = stash.call_GQL(query_studio_last_updated).get('findStudios',{}).get('studios',{})
    if len(studios)==0:
        return None
        
    studio=studios[0]
    return studio


def getScenesForStudio(stash: StashInterface, studio: int) -> list[dict]:
    query_scenes_by_studio = f"""
        query {{
            findScenes(scene_filter:{{studios:{{value:{studio},modifier:EQUALS}}}},filter:{{sort:"title",per_page:-1}}) {{
                scenes {{
                    id title details code studio {{name}} performers {{name gender}} files {{id basename path width height}} date
                }}
            }}
        }}
    """
    scenes = stash.call_GQL(query_scenes_by_studio).get('findScenes',{}).get('scenes',{})
    return scenes

def main():
    global defaultSettings
    global directoriesToScan

    stdin_input: str = sys.stdin.read()
    plugin: Plugin = Plugin('sceneFilesRenamer', stdin_input)
    json_input = json.loads(stdin_input)

    stash = getStash(json_input)
    
    settings = getSettings(stash, 'sceneFilesRenamer', defaultSettings)
    
    log.setup_file("sceneFilesRenamer.log", log.DEBUG if settings['debugTracing'] else log.INFO)

    template = Template(settings['renameTemplate'])
    template.callbacks['studio'] = renderStudio
    template.callbacks['performers'] = renderPerformers
    template.callbacks['date'] = renderDate
    
    settings['template'] = template
    if not checkSettings(settings):
        return

    args = json_input.get('args', {})
    hookContext = args.get('hookContext', {})
    mode = args.get('mode', '')
    
    if hookContext: # hook
        input = hookContext.get('input', None)
        if input is None:
            # we're being triggered a second time as a result of the stash.metadata_scan() call
            # so no need to call the rename logic
            return
        
        type = hookContext.get('type', '')
        if type == 'Scene.Update.Post':
            sceneId = hookContext.get('id', None)
            log.info(f"Scene.Update.Post(sceneId {sceneId})")
            
            if not sceneId:
                log.error(f"No scene passed")
                return
            
            scene = stash.find_scene(sceneId, "id title details code studio {name} performers {name gender} files {id basename path width height} date")
            if not scene:
                log.error(f"Scene {sceneId} not found")
                return
            
            renameSceneFiles(stash, settings, scene)
            if len(directoriesToScan) != 0:
                stash.metadata_scan(paths=[d for d in directoriesToScan])
                directoriesToScan.clear()
        else:
            log.error(f"unsupported args.hookContext.type {type}")
    elif mode: # task
        if mode == 'runForLastUpdatedStudio':
            settings['dryRun'] = False
            
            studio=findLastUpdatedStudio(stash)
            if studio is None:
                log.error(f"Last updated Studio not found")
                return

            log.info(f"runForLastUpdatedStudio(studio #{studio['id']} '{studio['name']}')")

            scenes = getScenesForStudio(stash, studio['id'])
            for scene in scenes:
                renameSceneFiles(stash, settings, scene)
            if len(directoriesToScan) != 0:
                stash.metadata_scan(paths=[d for d in directoriesToScan])
                directoriesToScan.clear()
            
        elif mode == 'dryRunForLastUpdatedStudio':
            settings['dryRun'] = True
            
            studio=findLastUpdatedStudio(stash)
            if studio is None:
                log.error(f"Last updated Studio not found")
                return

            log.info(f"runForLastUpdatedStudio(studio #{studio['id']} '{studio['name']}')")

            scenes = getScenesForStudio(stash, studio['id'])
            for scene in scenes:
                renameSceneFiles(stash, settings, scene)
            if len(directoriesToScan) != 0:
                stash.metadata_scan(paths=[d for d in directoriesToScan])
                directoriesToScan.clear()
           
        else:
            log.error(f"unsupported args.mode {mode}")


if __name__ == "__main__":
    main()
