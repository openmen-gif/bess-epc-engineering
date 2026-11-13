"""Print-sized HHIC market charts; data remains owned by market_report_content."""
from pathlib import Path

PURPLE = '#6428E6'
INK = '#282536'
MUTED = '#777184'
PALE = '#D7CEE9'
GRID = '#EDEAF2'
TEAL = '#197C80'
RISK = '#B66B54'


def draw_chart(definition):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.font_manager import FontProperties
    key, title, labels, values, unit, note = definition
    font_dir = Path(__file__).resolve().parents[1]/'vendor/hhic_word/fonts'
    regular = FontProperties(fname=str(font_dir/'Pretendard-Regular.otf'))
    bold = FontProperties(fname=str(font_dir/'Pretendard-Bold.otf'))
    fig = Figure(figsize=(8.4,2.65),dpi=240,facecolor='white')
    FigureCanvasAgg(fig)
    kind = ('waterfall' if key == 'cash' else
            'line' if key in ('efficiency','price') else 'horizontal')
    tag = '공개 전망' if key == 'forecast' else '발표 용량' if key == 'projects' else '비교 기준' if key == 'revision' else '분석 가정'
    fig.text(.025,.94,tag+'  /  '+unit,fontproperties=bold,fontsize=11,color=MUTED)
    insight = {
        'forecast': f'전망 간 증가율  {(values[1]/values[0]-1)*100:+.1f}%',
        'revision': '서로 다른 기준의 전망 비교',
        'scenarios': '성장률 가정별 2030년 규모',
        'capex': '세 경로 모두 순현재가치 음수',
        'cash': '거래 마진 − 운영비 = 영업현금',
        'efficiency': '같은 방전량에서 충전 손실 비교',
        'price': '구매가격 40 USD/MWh 고정',
        'projects': '준공 발표 사례, 현재 가동량 아님',
    }[key]
    fig.text(.975,.94,insight,ha='right',fontproperties=bold,fontsize=11,color=INK)
    if kind == 'horizontal':
        ax = fig.add_axes([.26,.19,.65,.62])
        colors = [PALE] * len(values)
        colors[1 if key in ('forecast','revision','capex','scenarios') else 0] = PURPLE
        if key == 'capex':
            colors = [PALE,PURPLE,PALE]
        bars = ax.barh(range(len(values)),values,height=.34,color=colors,zorder=3)
        ax.set_yticks(range(len(labels)),labels)
        ax.invert_yaxis()
        ax.set_ylim(len(values)-.5,-.5)
        extent = max(abs(v) for v in values)
        if min(values) < 0:
            ax.set_xlim(-extent*1.24,0)
        else:
            ax.set_xlim(0,extent*1.22)
        for bar,v in zip(bars,values):
            ax.annotate(f'{v:,.1f}',(v,bar.get_y()+bar.get_height()/2),
                        xytext=(-8 if v<0 else 8,0),textcoords='offset points',
                        va='center',ha='right' if v<0 else 'left',
                        fontproperties=bold,fontsize=12,color=INK)
        ax.xaxis.grid(True,color=GRID,linewidth=.7)
        ax.axvline(0,color=PALE,linewidth=.8,zorder=2)
    else:
        ax = fig.add_axes([.09,.22,.85,.58])
        x = list(range(len(values)))
        if kind == 'waterfall':
            gross,cost,net = values
            ax.bar(x,[gross,cost,net],bottom=[0,net,0],width=.44,
                   color=[PALE,RISK,TEAL],zorder=3)
            ax.plot([.22,.78],[gross,gross],color=PALE,linewidth=1)
            ax.plot([1.22,1.78],[net,net],color=PALE,linewidth=1)
            for i,(y,label) in enumerate([(gross,f'{gross:,.2f}'),(gross,f'−{cost:,.2f}'),(net,f'{net:,.2f}')]):
                ax.annotate(label,(i,y),xytext=(0,7),textcoords='offset points',
                            ha='center',fontproperties=bold,fontsize=12,color=INK)
        else:
            ax.plot(x,values,color=PURPLE,linewidth=2.3,zorder=3)
            ax.scatter(x,values,s=65,c=PURPLE,edgecolor='white',linewidth=1.7,zorder=4)
            for i,v in enumerate(values):
                ax.annotate(f'{v:,.2f}',(i,v),xytext=(0,10),textcoords='offset points',
                            ha='center',fontproperties=bold,fontsize=12,color=INK)
        ax.set_xticks(x,labels)
        ax.set_xlim(-.4,len(values)-.6)
        ax.set_ylim(min(0,min(values)*1.2),max(values)*1.35)
        ax.yaxis.grid(True,color=GRID,linewidth=.7)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both',length=0,pad=8,labelcolor=MUTED)
    for tick in ax.get_xticklabels()+ax.get_yticklabels():
        tick.set_fontproperties(regular)
        tick.set_fontsize(10.5)
    return fig,kind
