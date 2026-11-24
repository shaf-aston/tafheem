import { Config } from '@remotion/cli/config'

Config.setEntryPoint('./src/index.js')
Config.setVideoImageFormat('jpeg')
Config.setJpegQuality(95)
Config.setCodec('h264')
Config.setCrf(16)
Config.setPixelFormat('yuv420p')
Config.setBrowserExecutable(process.env.REMOTION_CHROME || null)
