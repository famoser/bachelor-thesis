test links for videos, artists
https://www.netflix.com/watch/70204286  
https://www.netflix.com/browse/person/30154850  
https://www.netflix.com/browse/person/30154847

a packet definition looks like this:

``` json
{
  "method": "stop",
  "playbackContextId": "E1-BQFRAAELEJaDwkfSC7pblMQjCCufs2qAplVLWYoXiFQdtwnlrRgiqo_rtJB53vfP7RfhnSVQeoxe12V1YW7uhiCypGx2Fe7Ts96YDnma_77GjaezgBonvxFXGGOWmbLaqxIsf6UAl9Jhdl-3Qkf17fGjT91pAD9BU3XmJ2A0nyYT00LuLy-8R16sHhh_efLl7GhVUvclezRaG6nLB7Z7EWhLpA9yIrMREad80pvkmhwSx0qVr2EXbqACAEIOhVo.",
  "playbackSessionId": "BAwArYPMt8j2DACwtjpaN1YAAA3a0W4XTATGZ1kAAAAAABOL_AAAAWKuiyv6AgAAAQNFMS1CUUZSQUFFTEVKYUR3a2ZTQzdwYmxNUWpDQ3VmczJxQXBsVkxXWW9YaUZRZHR3bmxyUmdpcW9fcnRKQjUzdmZQN1JmaG5TVlFlb3hlMTJWMVlXN3VoaUN5cEd4MkZlN1RzOTZZRG5tYV83N0dqYWV6Z0JvbnZ4RlhHR09XbWJMYXF4SXNmNlVBbDlKaGRsLTNRa2YxN2ZHalQ5MXBBRDlCVTNYbUoyQTBueVlUMDBMdUx5LThSMTZzSGhoX2VmTGw3R2hWVXZjbGV6UmFHNm5MQjdaN0VXaExwQTl5SXJNUkVhZDgwcHZrbWh3U3gwcVZyMkVYYnFBQ0FFSU9oVm8u",
  "xid": 15233467684684,
  "mediaId": "A:1:1;2;en;1;|V:2:1;2;;1281020;2;CE3;0;|T:1:1;1;NONE;0;1;",
  "type": "stop",
  "position": 264320,
  "playback": {
    "playTimes": {
      "total": 3319,
      "audio": [
        {
          "downloadableId": "626203993",
          "duration": 3319,
          "bitrate": 96
        }
      ],
      "video": [
        {
          "downloadableId": "625440750",
          "duration": 3319,
          "bitrate": 1100,
          "vmaf": 79
        }
      ]
    }
  },
  "timestamp": 1523346994006,
  "uiProfileGuid": "K3UWUOENKVDE5CQ7GCCQ4YUABU",
  "languages": [
    "en-CH"
  ],
  "clientVersion": "5.0008.781.011",
  "uiVersion": "akira"
}
````

bitrates for the specific profiles:
    E.V.ida:
        100, 175, 250, 500, 1350
    E.V.hB:
        120, 235, 375, 560, 750, 1050, 1750
    E.V.iB:
        2350, 3000
    E.V.vI:
        4300, 5800

video encoding:
  size of packets is always 4 seconds
  sound is longer, and always of the same size

shortcuts:
ctrl-alt-shift+d (68),ctrl-alt-shift+q (81) -> list with all current properties of video, audio
ctrl-alt-shift+s (83) -> menu allowing to choose video, audio, CDN
ctrl-alt-shift+t (84) -> file upload???
ctrl-alt-shift+i (73) ->
ctrl-alt-shift+l (76) -> log console

further resources:
includes handshake & crypto, may be able to directly save streams
https://github.com/asciidisco/plugin.video.netflix/blob/master/resources/lib/MSL.py

