/** items.csv + LLM general_items 아이콘 — MDI 아웃라인 단일 무드 */

import earlySummerImage from '../../assets/images/early_summer.webp'
import aquaShoesImage from '../../assets/images/aquaShoes-transparent.png'
import antiTheftStrapImage from '../../assets/images/antiTheftStrap-transparent.png'
import backpackImage from '../../assets/images/backpack-transparent.png'
import bandageImage from '../../assets/images/bandage-transparent.png'
import batteryImage from '../../assets/images/battery-transparent.png'
import bootsImage from '../../assets/images/boots-transparent.png'
import chargerImage from '../../assets/images/charger-transparent.png'
import coinPurseImage from '../../assets/images/coinPurse-transparent.png'
import document1Image from '../../assets/images/document1-transparent.png'
import document2Image from '../../assets/images/document2-transparent.png'
import kneePadsImage from '../../assets/images/kneePads-transparent.png'
import linenPantsImage from '../../assets/images/linenPants-transparent.png'
import lockImage from '../../assets/images/lock-transparent.png'
import lotionImage from '../../assets/images/lotion-transparent.png'
import makeUpImage from '../../assets/images/makeUp-transparent.png'
import medicineImage from '../../assets/images/medicine-transparent.png'
import maskImage from '../../assets/images/mask-transparent.png'
import medkitImage from '../../assets/images/medkit-transparent.png'
import mouthwashImage from '../../assets/images/Mouthwash-transparent.png'
import mosquitoImage from '../../assets/images/mosquito-transparent.png'
import multitoolImage from '../../assets/images/multitool-transparent.png'
import notePenImage from '../../assets/images/notePen-transparent.png'
import pajamasImage from '../../assets/images/pajamas-transparent.png'
import pantsImage from '../../assets/images/pants-transparent.png'
import passportImage from '../../assets/images/passport-transparent.png'
import razorImage from '../../assets/images/razor-transparent.png'
import raincoatImage from '../../assets/images/raincoat-transparent.png'
import remoteImage from '../../assets/images/remote-transparent.png'
import rfidWalletImage from '../../assets/images/rfid_wallet-transparent.png'
import showerImage from '../../assets/images/shower-transparent.png'
import showerGelImage from '../../assets/images/showerGel-transparent.png'
import slipperImage from '../../assets/images/slipper.png'
import socksImage from '../../assets/images/socks-transparent.png'
import springImage from '../../assets/images/spring-transparent.png'
import sanitizerImage from '../../assets/images/sanitizer-transparent.png'
import sunscreenImage from '../../assets/images/sunscreen-transparent.png'
import summerImage from '../../assets/images/summer.png'
import sunglassImage from '../../assets/images/sunglass-transparent.png'
import tanktopImage from '../../assets/images/tanktop-transparent.png'
import toothbrushImage from '../../assets/images/toothbrush-transparent.png'
import towelImage from '../../assets/images/towel-transparent.png'
import travelAdapterImage from '../../assets/images/travelAdapter-transparent.png'
import tumblerImage from '../../assets/images/tumbler-transparent.png'
import tripodImage from '../../assets/images/tripod-transparent.png'
import tshirtImage from '../../assets/images/tshirt-transparent.png'
import umbrellaImage from '../../assets/images/umbrella-transparent.png'
import portableFanImage from '../../assets/images/portableFan-transparent.png'
import walkingStickImage from '../../assets/images/walkingStick-transparent.png'
import waxImage from '../../assets/images/wax-transparent.png'
import waterproofDryBagImage from '../../assets/images/waterproofDryBag-transparent.png'
import waterproofPouchImage from '../../assets/images/waterproofPouch-transparent.png'
import wetTissueImage from '../../assets/images/wetTissue-transparent.png'
import winterImage from '../../assets/images/winter-transparent.png'

const ICON_COLOR = '%231a535c'
const ICON_SIZE = 96

/** 카테고리 기본 (아웃라인·라인 스타일 우선) */
export const CATEGORY_ICONS = {
  clothing: 'mdi:tshirt-crew-outline',
  toiletries: 'mdi:hand-wash-outline',
  electronics: 'mdi:cellphone-link',
  documents: 'mdi:passport',
  accessories: 'mdi:bag-personal-outline',
  health: 'mdi:pill',
  other: 'mdi:bag-suitcase-outline',
}

/** 이름 키워드 매칭 — LLM이 만든 general_items용 (앞쪽 우선) */
const KEYWORD_ICON_RULES = [
  [/칫솔|치약|구강|치실|가글|세트.*(칫|치)/, 'mdi:toothbrush'],
  [/진통|소화|밴드|상비약|의약|약품|감기|지설|의료/, 'mdi:pill'],
  [/우비|우산/, 'mdi:umbrella-outline'],
  [/파우치|방수.*백|드라이백/, 'mdi:bag-personal-outline'],
  [/충전|배터리|어댑터|케이블|멀티콘센트|콘센트|이어폰|리모컨/, 'mdi:cellphone-link'],
  [/여권|신분증|항공권|비자|서류|증명/, 'mdi:passport'],
  [/세면|세면도구|샤워|클렌저|수건|타월/, 'mdi:shower-head'],
  [/선크림|SPF|자외선/, 'mdi:white-balance-sunny'],
  [/면도|쉐이빙|그루밍|왁스|포마드/, 'mdi:razor-double-edge'],
  [/생리/, 'mdi:flower-outline'],
  [/화장|메이크업|스킨|로션|크림|뷰티/, 'mdi:lipstick'],
  [/속옷|양말|잠옷|상의|하의|의류|티셔츠|셔츠|바지|니트|자켓|외투|코트|린넨/, 'mdi:tshirt-crew-outline'],
  [/물티슈|티슈|휴지/, 'mdi:paper-roll-outline'],
  [/마스크/, 'mdi:face-mask-outline'],
  [/우산|우비|비|눈|장갑|핫팩|손난로|방한/, 'mdi:umbrella-outline'],
  [/물병|텀블러/, 'mdi:bottle-soda-classic-outline'],
  [/고추장|한식/, 'mdi:bottle-tonic-outline'],
  [/자물쇠|도난|RFID|지갑/, 'mdi:lock-outline'],
  [/슬리퍼|신발|슈즈/, 'mdi:shoe-formal'],
  [/수영/, 'mdi:swim'],
  [/등산|트레킹|스틱|하이킹/, 'mdi:hiking'],
  [/모기|기피|벌레/, 'mdi:mosquito'],
  [/선글라스|모자/, 'mdi:sunglasses'],
  [/침낭|라이너|침구/, 'mdi:bed-outline'],
  [/압축|패킹/, 'mdi:bag-suitcase-outline'],
]

export const ITEM_ICONS = {
  '유선 이어폰': 'mdi:headphones',
  '미니 삼각대': 'mdi:camera-tripod',
  '블루투스 리모컨': 'mdi:remote',
  '접이식 에코백': 'mdi:shopping-outline',
  '동전 지갑': 'mdi:wallet-outline',
  '방수 파우치': 'mdi:bag-personal-outline',
  '스포츠 타월': 'mdi:beach',
  '친환경 선크림': 'mdi:white-balance-sunny',
  '방수 드라이백': 'mdi:bag-carry-on',
  '아쿠아 슈즈': 'mdi:shoe-formal',
  '얇은 스카프': 'mdi:ribbon',
  '린넨 긴바지': 'mdi:tshirt-crew-outline',
  '편한 슬립온': 'mdi:shoe-sneaker',
  '보조 배터리': 'mdi:battery-charging-high',
  '오페라글래스': 'mdi:binoculars',
  '접이식 방석': 'mdi:seat-outline',
  '무릎 보호대': 'mdi:bandage',
  '접이식 등산스틱': 'mdi:hiking',
  '모기 기피제': 'mdi:mosquito',
  '휴대용 물티슈': 'mdi:paper-roll-outline',
  '압박 밴드': 'mdi:sock',
  '쿨링 패치': 'mdi:snowflake',
  '멀티툴': 'mdi:knife-military',
  '접이식 돗자리': 'mdi:rug',
  '도난방지 스트랩': 'mdi:link-variant',
  '바람막이 자켓': 'mdi:coat-rack',
  '선글라스와 모자': 'mdi:sunglasses',
  '드라이 샴푸': 'mdi:spray',
  '포켓 수첩과 펜': 'mdi:notebook-edit-outline',
  '텀블러 백': 'mdi:cup-outline',
  '와이어 자물쇠': 'mdi:lock-outline',
  '귀마개와 안대': 'mdi:sleep',
  '미니 세면도구': 'mdi:hand-wash-outline',
  '수영복': 'mdi:swim',
  '필터 샤워기': 'mdi:shower-head',
  '일회용 위생커버': 'mdi:bed-outline',
  '튜브형 고추장': 'mdi:bottle-tonic-outline',
  '접이식 슬리퍼': 'mdi:shoe-ballet',
  '비상 상비약': 'mdi:pill',
  '의류 압축팩': 'mdi:bag-suitcase-outline',
  '미니 멀티콘센트': 'mdi:power-plug-outline',
  '핫팩 및 손난로': 'mdi:fire',
  '목걸이 선풍기': 'mdi:fan',
  '재사용 물병': 'mdi:bottle-soda-classic-outline',
  '경량 우비': 'mdi:umbrella-outline',
  'SPF100선크림': 'mdi:white-balance-sunny',
  '고보습 헤어팩': 'mdi:hair-dryer-outline',
  '고산병 약': 'mdi:pill',
  '방진 마스크': 'mdi:face-mask-outline',
  'RFID 지갑': 'mdi:credit-card-lock-outline',
  '빈대 퇴치제': 'mdi:bug-outline',
  '침낭 라이너': 'mdi:bed-outline',
  '비데 물티슈': 'mdi:toilet-paper',
  '봄가을 의류 세트': 'mdi:tshirt-crew-outline',
  '초여름 의류 세트': 'mdi:tshirt-crew-outline',
  '한여름 의류 세트': 'mdi:tshirt-crew-outline',
  '한겨울 의류 세트': 'mdi:coat-rack',
  '선크림': 'mdi:white-balance-sunny',
  '우산': 'mdi:umbrella-outline',
  '방수 신발': 'mdi:shoe-formal',
  '방수 장갑': 'mdi:hand-back-left-outline',
}

const ITEM_IMAGE_RULES = [
  [/생리대|생리|탐폰|팬티라이너|월경/, medkitImage],
  [/무릎.*보호대|니패드|무릎패드/, kneePadsImage],
  [/멀티툴|멀티.*툴|툴나이프/, multitoolImage],
  [/목걸이.*선풍기|휴대용.*선풍기|미니.*선풍기|선풍기|팬/, portableFanImage],
  [/모기|기피|벌레/, mosquitoImage],
  [/압박.*밴드|반창고|밴드/, bandageImage],
  [/여권|신분증|비자/, passportImage],
  [/항공권|티켓|예약.*확인|바우처|보험/, document2Image],
  [/서류|증명|문서|복사본|프린트/, document1Image],
  [/선크림|SPF|자외선/, sunscreenImage],
  [/면도|면도기|쉐이빙|그루밍/, razorImage],
  [/로션|스킨|크림|보습|헤어팩/, lotionImage],
  [/화장|메이크업|립스틱|뷰티/, makeUpImage],
  [/도난방지.*스트랩|도난.*스트랩|안티.*스트랩|스트랩/, antiTheftStrapImage],
  [/보조.*배터리|배터리|파워뱅크/, batteryImage],
  [/삼각대|트라이포드/, tripodImage],
  [/방수.*드라이백|드라이백/, waterproofDryBagImage],
  [/방수.*파우치|방수팩/, waterproofPouchImage],
  [/물티슈|티슈|휴지/, wetTissueImage],
  [/텀블러|물병|보틀/, tumblerImage],
  [/아쿠아.*슈즈|아쿠아.*신발/, aquaShoesImage],
  [/비옷|레인코트|우비/, raincoatImage],
  [/우산|양산|비옷|레인코트/, umbrellaImage],
  [/타월|수건/, towelImage],
  [/구강청결제|가글|마우스워시|입가심/, mouthwashImage],
  [/칫솔|치약|양치/, toothbrushImage],
  [/샤워젤|샤워.*젤|바디워시|바디.*워시|바디클렌저/, showerGelImage],
  [/부츠|장화|방수.*신발|방수.*부츠/, bootsImage],
  [/마스크|방진/, maskImage],
  [/손소독제|소독제|위생젤|핸드젤/, sanitizerImage],
  [/백팩|배낭|데이팩/, backpackImage],
  [/등산스틱|트레킹폴|트레킹.*스틱|하이킹.*스틱/, walkingStickImage],
  [/상비약|비상약|의약품|진통|소화제|감기약|구급|밴드/, medicineImage],
  [/자물쇠|잠금|와이어.*자물쇠/, lockImage],
  [/동전|동전지갑|코인|코인퍼스/, coinPurseImage],
  [/리모컨|리모콘|블루투스.*리모컨|블루투스.*리모콘/, remoteImage],
  [/왁스|포마드|헤어.*왁스/, waxImage],
  [/수첩|노트|메모|펜|필기/, notePenImage],
  [/린넨/, linenPantsImage],
  [/RFID|지갑/, rfidWalletImage],
  [/여행.*어댑터|어댑터|멀티콘센트|멀티.*콘센트|콘센트|플러그/, travelAdapterImage],
  [/충전|배터리|어댑터|케이블|멀티콘센트|콘센트/, chargerImage],
  [/선글라스/, sunglassImage],
  [/슬리퍼|샌들|실내화/, slipperImage],
  [/양말/, socksImage],
  [/잠옷|파자마/, pajamasImage],
  [/속옷|민소매|나시|탱크톱|탱크탑/, tanktopImage],
  [/바지|하의|린넨/, pantsImage],
  [/필터 샤워기|샤워|세면/, showerImage],
  [/봄가을|바람막이|재킷|자켓/, springImage],
  [/한여름|반팔/, summerImage],
  [/상의/, tshirtImage],
  [/초여름|긴팔|셔츠/, earlySummerImage],
  [/한겨울|패딩|외투|코트/, winterImage],
]

export const CATEGORY_HEX = {
  clothing: '#d4e8f0',
  toiletries: '#e8dff8',
  electronics: '#ffe8cc',
  documents: '#d8f0e0',
  accessories: '#f8dce8',
  health: '#fff8d0',
  other: '#ececec',
}

export const CATEGORY_STYLES = {
  clothing: { bg: '#d4e8f0', border: '#9ec5d8' },
  toiletries: { bg: '#e8dff8', border: '#b8a0e0' },
  electronics: { bg: '#ffe8cc', border: '#e0b878' },
  documents: { bg: '#d8f0e0', border: '#88c8a0' },
  accessories: { bg: '#f8dce8', border: '#e0a8c0' },
  health: { bg: '#fff8d0', border: '#d8c060' },
  other: { bg: '#ececec', border: '#c8c8c8' },
}

export function getIconId(name, category = 'other') {
  const text = String(name || '').trim()
  if (text && ITEM_ICONS[text]) return ITEM_ICONS[text]

  for (const [pattern, icon] of KEYWORD_ICON_RULES) {
    if (pattern.test(text)) return icon
  }

  return CATEGORY_ICONS[category] || CATEGORY_ICONS.other
}

export function getItemImageUrl(name) {
  const text = String(name || '').trim()
  for (const [pattern, image] of ITEM_IMAGE_RULES) {
    if (pattern.test(text)) return image
  }
  return null
}

export function getIllustrationUrl(name, category = 'other', iconId = null) {
  const icon = iconId || getIconId(name, category)
  const [prefix, iconName] = icon.split(':')
  return `https://api.iconify.design/${prefix}/${iconName}.svg?width=${ICON_SIZE}&height=${ICON_SIZE}&color=${ICON_COLOR}`
}
